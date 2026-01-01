import os
import sys

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


def test_end_to_end_pipeline_trace():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    # Use internal API to force set the provider for testing.
    trace._TRACER_PROVIDER = provider

    old_enable_otlp = os.environ.get("ENABLE_OTLP")
    os.environ["ENABLE_OTLP"] = "false"

    modules_to_reload = [
        "ebpf_bot.coverage_bot",
        "ebpf_bot.orchestrator",
        "ebpf_bot.processor",
        "ebpf_bot.store",
        "ebpf_bot.pipeline",
    ]
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            del sys.modules[module_name]

    try:
        from ebpf_bot.pipeline import UnifiedPipeline

        pipeline = UnifiedPipeline()
        pipeline.collect_and_decide()

        spans = exporter.get_finished_spans()
        span_names = [span.name for span in spans]
        print("Generated spans:", span_names)

        assert "unified_pipeline_decision" in span_names
        assert "decide_next_probe" in span_names
        assert any(name.startswith("store_") for name in span_names)
        assert any(name.startswith("process_") for name in span_names)

        pipeline_span = next(span for span in spans if span.name == "unified_pipeline_decision")
        coverage_span = next(span for span in spans if span.name == "get_coverage")
        orchestrator_span = next(span for span in spans if span.name == "decide_next_probe")

        assert pipeline_span.attributes.get("pipeline.coverage_signals") is not None
        assert pipeline_span.attributes.get("pipeline.coverage_count") is not None
        assert pipeline_span.attributes.get("pipeline.next_probe") is not None
        assert any(event.name == "coverage_received" for event in pipeline_span.events)
        assert any(event.name == "decision_made" for event in pipeline_span.events)

        assert coverage_span.attributes.get("coverage_bot.expected_signals") is not None
        assert any(event.name == "fetching_coverage_map" for event in coverage_span.events)

        assert orchestrator_span.attributes.get("orchestrator.strategy") is not None
        assert orchestrator_span.attributes.get("orchestrator.coverage_map") is not None
        assert orchestrator_span.attributes.get("orchestrator.chosen_probe") is not None
        assert any(event.name == "probe_decided" for event in orchestrator_span.events)
    finally:
        if old_enable_otlp is not None:
            os.environ["ENABLE_OTLP"] = old_enable_otlp
        else:
            os.environ.pop("ENABLE_OTLP", None)
