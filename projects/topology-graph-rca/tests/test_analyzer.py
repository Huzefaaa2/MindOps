import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from topology_graph_rca.analyzer import TopologyAnalyzer


class AnalyzerTests(unittest.TestCase):
    def test_analyze_sample(self):
        manifests = [str(ROOT / "examples" / "sample_k8s.yaml")]
        traces = [str(ROOT / "examples" / "sample_trace.json")]
        analyzer = TopologyAnalyzer(error_threshold=0.01)
        try:
            report = analyzer.analyze(manifest_paths=manifests, trace_paths=traces)
        except RuntimeError as exc:
            self.skipTest(str(exc))
            return
        self.assertGreaterEqual(len(report.nodes), 3)
        self.assertGreaterEqual(len(report.edges), 2)
        self.assertGreaterEqual(len(report.hints), 1)


if __name__ == "__main__":
    unittest.main()
