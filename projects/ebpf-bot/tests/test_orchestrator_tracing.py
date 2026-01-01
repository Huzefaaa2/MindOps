import sys

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


def test_orchestrator_tracing_creates_span():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    # Use internal API to force set the provider for testing.
    trace._TRACER_PROVIDER = provider

    if "ebpf_bot.orchestrator" in sys.modules:
        del sys.modules["ebpf_bot.orchestrator"]

    from ebpf_bot.orchestrator import CoverageOrchestrator

    orchestrator = CoverageOrchestrator()
    orchestrator.decide_next_probe({"probe_a": False})

    spans = exporter.get_finished_spans()
    span_names = [span.name for span in spans]

    assert "decide_next_probe" in span_names
