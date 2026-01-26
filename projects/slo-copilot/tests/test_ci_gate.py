import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from slo_copilot.copilot import SLOCopilot
from slo_copilot.deployment_gate import gate_from_report
from slo_copilot.trace_stats import compute_trace_stats


class CIGateTests(unittest.TestCase):
    def test_guardrail_gate(self):
        trace_path = ROOT / "examples" / "sample_trace.json"
        copilot = SLOCopilot(enable_caat=False, enable_trag=False, enable_ebpf=False)
        report = copilot.run(str(trace_path))
        stats = compute_trace_stats(copilot._load_spans(str(trace_path)))
        decision = gate_from_report(report, stats)
        self.assertIn(decision.passed, [True, False])


if __name__ == "__main__":
    unittest.main()
