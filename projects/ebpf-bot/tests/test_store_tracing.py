import sys

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


def test_store_tracing_spans_created():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    # Use internal API to force set the provider for testing.
    trace._TRACER_PROVIDER = provider

    if "ebpf_bot.store" in sys.modules:
        del sys.modules["ebpf_bot.store"]

    from ebpf_bot.store import SignalStore

    store = SignalStore()
    store.save("probe_a", {"latency": 42})
    store.load("probe_a")

    spans = exporter.get_finished_spans()
    assert any(span.name == "store_save_signal" for span in spans)
    assert any(span.name == "store_load_signal" for span in spans)
