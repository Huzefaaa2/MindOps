import sys

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


def test_receiver_tracing_span_created():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    # Use internal API to force set the provider for testing.
    trace._TRACER_PROVIDER = provider

    if "ebpf_bot.receiver" in sys.modules:
        del sys.modules["ebpf_bot.receiver"]

    from ebpf_bot.receiver import SignalReceiver

    receiver = SignalReceiver()
    receiver.receive("event_123")

    spans = exporter.get_finished_spans()
    assert any(span.name == "receive_signal" for span in spans)
