# store.py

from opentelemetry import trace

tracer = trace.get_tracer(__name__)


class SignalStore:
    def __init__(self) -> None:
        self.db = {}

    def save(self, signal_id: str, signal_data: dict) -> bool:
        with tracer.start_as_current_span("store_save_signal"):
            self.db[signal_id] = signal_data
            return True

    def load(self, signal_id: str):
        with tracer.start_as_current_span("store_load_signal"):
            return self.db.get(signal_id)
