from opentelemetry import trace

tracer = trace.get_tracer(__name__)


class CoverageBot:
    def __init__(self, expected_signals):
        self.expected_signals = expected_signals
        self.coverage_map = {signal: False for signal in expected_signals}
        print(f"[CoverageBot] Initialized with expected signals: {expected_signals}")

    def observe(self, signal):
        print(f"[CoverageBot] Observing signal: {signal}")
        if signal in self.coverage_map:
            self.coverage_map[signal] = True
            print(f"[CoverageBot] Signal '{signal}' marked as observed.")
        else:
            print(f"[CoverageBot] Signal '{signal}' not expected.")

    def coverage_score(self):
        covered = sum(self.coverage_map.values())
        total = len(self.coverage_map)
        score = covered / total if total else 0
        print(f"[CoverageBot] Coverage score: {score:.2f}")
        return score

    def get_coverage(self):
        with tracer.start_as_current_span("get_coverage") as span:
            span.add_event("fetching_coverage_map")
            print("[CoverageBot] Returning current coverage map...")
            span.set_attribute("coverage_bot.expected_signals", list(self.coverage_map.keys()))
            return self.coverage_map

    def find_missing_signals(self, observed_signals):
        missing = [s for s in self.expected_signals if s not in observed_signals]
        return missing

    def suggest_instrumentation(self, missing_signals):
        print(f"[CoverageBot] Suggesting instrumentation for: {missing_signals}")
        return [f"Add eBPF probe for '{signal}'" for signal in missing_signals]
