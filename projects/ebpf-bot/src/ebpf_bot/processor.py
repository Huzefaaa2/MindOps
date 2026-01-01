# processor.py

from opentelemetry import trace

tracer = trace.get_tracer(__name__)


class SignalProcessor:
    def process(self, signal: str) -> dict:
        with tracer.start_as_current_span("process_signal"):
            print(f"[Processor] Processing signal: {signal}")
            return {"status": "processed", "signal": signal}
