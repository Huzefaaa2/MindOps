# receiver.py

from opentelemetry import trace

tracer = trace.get_tracer(__name__)


class SignalReceiver:
    def receive(self, signal: str) -> bool:
        with tracer.start_as_current_span("receive_signal"):
            print(f"[Receiver] Received signal: {signal}")
            return True
