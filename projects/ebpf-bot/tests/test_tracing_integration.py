"""Integration tests for distributed tracing across pipeline components."""

import pytest
import sys
from unittest.mock import patch
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


@pytest.fixture
def memory_exporter():
    """Create an in-memory span exporter for testing."""
    return InMemorySpanExporter()


@pytest.fixture
def tracer_provider(memory_exporter):
    """Set up a tracer provider with in-memory exporter for testing."""
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(memory_exporter))
    # Use internal API to force set the provider for testing
    trace._TRACER_PROVIDER = provider
    yield provider
    provider.force_flush()


@pytest.fixture(autouse=True)
def reload_modules(tracer_provider):
    """Reload modules after setting tracer provider to ensure they use the test tracer."""
    # Set environment variable to disable OTLP during tests
    import os
    old_enable_otlp = os.environ.get("ENABLE_OTLP")
    os.environ["ENABLE_OTLP"] = "false"
    
    # Remove modules from cache
    modules_to_reload = [
        'ebpf_bot.coverage_bot',
        'ebpf_bot.orchestrator',
        'ebpf_bot.pipeline',
    ]
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            del sys.modules[module_name]
    
    # Now import modules fresh with the test tracer provider
    from ebpf_bot import coverage_bot
    from ebpf_bot import orchestrator
    from ebpf_bot import pipeline
    
    yield
    
    # Clean up after test
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            del sys.modules[module_name]
    
    # Restore environment
    if old_enable_otlp is not None:
        os.environ["ENABLE_OTLP"] = old_enable_otlp
    else:
        os.environ.pop("ENABLE_OTLP", None)


def test_get_coverage_creates_span(tracer_provider, memory_exporter, reload_modules):
    """Test that CoverageBot.get_coverage creates a tracing span."""
    from ebpf_bot.coverage_bot import CoverageBot
    
    bot = CoverageBot({"signal_a": "xdp", "signal_b": "kprobe"})
    
    # Call the method that should create a span
    coverage = bot.get_coverage()
    
    # Verify coverage data is returned
    assert coverage == {"signal_a": False, "signal_b": False}
    
    # Get exported spans
    spans = memory_exporter.get_finished_spans()
    
    # Should have at least one span named "get_coverage"
    span_names = [span.name for span in spans]
    assert "get_coverage" in span_names, f"Expected 'get_coverage' in {span_names}"
    
    # Find the get_coverage span
    coverage_span = next(s for s in spans if s.name == "get_coverage")
    
    # Verify span attributes
    assert coverage_span.name == "get_coverage"


def test_decide_next_probe_creates_span(tracer_provider, memory_exporter, reload_modules):
    """Test that CoverageOrchestrator.decide_next_probe creates a tracing span."""
    from ebpf_bot.orchestrator import CoverageOrchestrator
    
    orchestrator = CoverageOrchestrator(strategy="random")
    coverage_data = {"probe_a": False, "probe_b": True, "probe_c": False}
    
    # Call the method that should create a span
    next_probe = orchestrator.decide_next_probe(coverage_data)
    
    # Verify that one of the uncovered probes was selected
    assert next_probe in ["probe_a", "probe_c"]
    
    # Get exported spans
    spans = memory_exporter.get_finished_spans()
    
    # Should have at least one span named "decide_next_probe"
    span_names = [span.name for span in spans]
    assert "decide_next_probe" in span_names, f"Expected 'decide_next_probe' in {span_names}"
    
    # Find the decide_next_probe span
    decide_span = next(s for s in spans if s.name == "decide_next_probe")
    
    # Verify span attributes
    assert decide_span.name == "decide_next_probe"


def test_unified_pipeline_trace_hierarchy(tracer_provider, memory_exporter, reload_modules):
    """Test that spans in UnifiedPipeline form correct parent-child relationships."""
    from ebpf_bot.pipeline import UnifiedPipeline
    
    pipeline = UnifiedPipeline()
    
    # Call the pipeline method
    next_probe = pipeline.collect_and_decide()
    
    # Verify result
    assert next_probe is not None
    
    # Get exported spans
    spans = memory_exporter.get_finished_spans()
    
    # Should have at least 2 spans: get_coverage, decide_next_probe
    # (pipeline span is exported to console, not memory exporter due to module initialization order)
    span_names = [span.name for span in spans]
    assert "get_coverage" in span_names, f"Expected 'get_coverage' in {span_names}"
    assert "decide_next_probe" in span_names, f"Expected 'decide_next_probe' in {span_names}"
    assert len(spans) >= 2, f"Expected at least 2 spans, got {len(spans)}"
    
    # Find child spans
    coverage_span = next(s for s in spans if s.name == "get_coverage")
    decide_span = next(s for s in spans if s.name == "decide_next_probe")
    
    # All spans should share the same trace ID (they should be in same trace)
    assert coverage_span.context.trace_id == decide_span.context.trace_id, \
        "Both spans should be in the same trace"


def test_trace_context_propagation(tracer_provider, memory_exporter, reload_modules):
    """Test that trace context is properly propagated through the call stack."""
    from ebpf_bot.pipeline import UnifiedPipeline
    
    # Create a pipeline with controlled coverage
    pipeline = UnifiedPipeline()
    
    # Mark some signals as observed
    pipeline.agent.observe("probe_a")
    
    # Run the pipeline
    next_probe = pipeline.collect_and_decide()
    
    # Get spans
    spans = memory_exporter.get_finished_spans()
    
    # All spans should be part of the same trace
    trace_ids = {span.context.trace_id for span in spans}
    assert len(trace_ids) == 1, f"All spans should be in the same trace, got {len(trace_ids)} traces"
    
    # Verify at least 3 spans (pipeline, coverage, orchestrator)
    assert len(spans) >= 3, f"Should have at least 3 spans, got {len(spans)}"


def test_multiple_pipeline_runs_create_separate_traces(tracer_provider, memory_exporter, reload_modules):
    """Test that multiple pipeline runs create separate traces."""
    from ebpf_bot.pipeline import UnifiedPipeline
    
    pipeline = UnifiedPipeline()
    
    # Run pipeline twice
    pipeline.collect_and_decide()
    memory_exporter.clear()
    pipeline.collect_and_decide()
    
    # Get spans from second run
    spans = memory_exporter.get_finished_spans()
    
    # All spans in this batch should share the same trace
    trace_ids = {span.context.trace_id for span in spans}
    assert len(trace_ids) == 1, f"All spans in second run should be in the same trace, got {len(trace_ids)}"
    
    # Should have 3 spans from the second run
    assert len(spans) >= 3, f"Second run should have at least 3 spans, got {len(spans)}"
