import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mindops_orchestrator.cli import _export_structured


class OrchestratorTests(unittest.TestCase):
    def test_export_structured(self):
        report = {"zero_touch": {"collector": {}}, "slo_copilot": {"foo": "bar"}, "warnings": []}
        with TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir)
            _export_structured(out_dir, report=report, zero_touch=report["zero_touch"], slo_report=report["slo_copilot"])
            self.assertTrue((out_dir / "orchestrator_report.json").exists())
            self.assertTrue((out_dir / "zero_touch" / "plan.json").exists())
            self.assertTrue((out_dir / "slo_copilot" / "report.json").exists())


if __name__ == "__main__":
    unittest.main()
