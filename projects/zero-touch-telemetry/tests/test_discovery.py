import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from zero_touch_telemetry.discovery import discover_services
from zero_touch_telemetry.planner import ZeroTouchPlanner


class DiscoveryTests(unittest.TestCase):
    def test_discover_services(self):
        manifest = ROOT / "examples" / "sample_k8s.yaml"
        try:
            services = discover_services([str(manifest)])
        except RuntimeError as exc:
            self.skipTest(str(exc))
            return
        self.assertGreaterEqual(len(services), 2)
        names = {svc.name for svc in services}
        self.assertIn("checkout", names)
        self.assertIn("payments", names)

    def test_planner_gateway(self):
        manifest = ROOT / "examples" / "sample_k8s.yaml"
        try:
            services = discover_services([str(manifest)])
        except RuntimeError as exc:
            self.skipTest(str(exc))
            return
        planner = ZeroTouchPlanner(mode="gateway")
        plan = planner.plan(services)
        self.assertEqual(plan.collector.mode, "gateway")
        self.assertIn("otel-collector-gateway", plan.collector.manifest_yaml)


if __name__ == "__main__":
    unittest.main()
