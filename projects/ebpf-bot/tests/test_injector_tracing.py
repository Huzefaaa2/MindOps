import sys

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


def test_injector_creates_span():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    # Use internal API to force set the provider for testing.
    trace._TRACER_PROVIDER = provider

    if "ebpf_bot.injector" in sys.modules:
        del sys.modules["ebpf_bot.injector"]

    from ebpf_bot.injector import ProbeInjector

    injector = ProbeInjector()
    injector.inject_probe("probe_z")

    spans = exporter.get_finished_spans()
    assert any(span.name == "inject_probe" for span in spans)
