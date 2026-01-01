# injector.py

from opentelemetry import trace

tracer = trace.get_tracer(__name__)


class ProbeInjector:
    def inject_probe(self, probe: str) -> bool:
        with tracer.start_as_current_span("inject_probe"):
            print(f"[Injector] Injecting probe: {probe}")
            return True
