# orchestrator.py

import random
from opentelemetry import trace

tracer = trace.get_tracer(__name__)


class CoverageOrchestrator:
    def __init__(self, strategy: str = "random"):
        self.strategy = strategy

    def decide_next_probe(self, coverage_data: dict) -> str:
        with tracer.start_as_current_span("decide_next_probe") as span:
            span.set_attribute("orchestrator.strategy", self.strategy)
            span.set_attribute("orchestrator.coverage_map", str(coverage_data))

            missing = [probe for probe, signal in coverage_data.items() if not signal]
            chosen = random.choice(missing) if missing else random.choice(list(coverage_data.keys()))
            span.set_attribute("orchestrator.chosen_probe", chosen)
            span.add_event("probe_decided", {"chosen": chosen})
            print(f"[Orchestrator] Using strategy '{self.strategy}' to decide next probe.")
            return chosen
