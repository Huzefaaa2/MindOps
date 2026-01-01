import sys

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


def test_processor_tracing_span_created():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    # Use internal API to force set the provider for testing.
    trace._TRACER_PROVIDER = provider

    if "ebpf_bot.processor" in sys.modules:
        del sys.modules["ebpf_bot.processor"]

    from ebpf_bot.processor import SignalProcessor

    processor = SignalProcessor()
    processor.process("event_abc")

    spans = exporter.get_finished_spans()
    assert any(span.name == "process_signal" for span in spans)
