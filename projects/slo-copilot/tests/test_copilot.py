import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from slo_copilot.copilot import SLOCopilot
from slo_copilot.exports import export_open_slo, export_slo_json
from slo_copilot.openslo_yaml import export_open_slo_yaml


class SLOCopilotTests(unittest.TestCase):
    def test_run_with_sample_trace(self):
        trace_path = ROOT / "examples" / "sample_trace.json"
        self.assertTrue(trace_path.exists())
        copilot = SLOCopilot(enable_caat=False, enable_trag=False, enable_ebpf=False)
        report = copilot.run(str(trace_path))
        self.assertGreater(len(report.slo_candidates), 0)
        self.assertGreater(len(report.baseline_evaluations), 0)
        self.assertGreater(len(report.test_results), 0)
        serialized = json.loads(json.dumps(report, default=lambda o: o.__dict__))
        self.assertIn("slo_candidates", serialized)

    def test_exports(self):
        trace_path = ROOT / "examples" / "sample_trace.json"
        copilot = SLOCopilot(enable_caat=False, enable_trag=False, enable_ebpf=False)
        report = copilot.run(str(trace_path))
        exported = export_slo_json(report.slo_candidates)
        self.assertIn("schema_version", exported)
        self.assertIn("slos", exported)
        openslo = export_open_slo(report.slo_candidates)
        self.assertGreater(len(openslo), 0)
        kinds = {item.get("kind") for item in openslo}
        self.assertIn("Service", kinds)
        self.assertIn("SLI", kinds)
        self.assertIn("SLO", kinds)
        yaml_export = export_open_slo_yaml(report.slo_candidates)
        self.assertIn("kind: Service", yaml_export)
        self.assertIn("kind: SLO", yaml_export)


if __name__ == "__main__":
    unittest.main()
