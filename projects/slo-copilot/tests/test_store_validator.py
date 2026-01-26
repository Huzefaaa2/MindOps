import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from slo_copilot.exports import export_open_slo
from slo_copilot.openslo_validator import validate_openslo_payload
from slo_copilot.slo_store import SLOStore
from slo_copilot.models import SLO, SLOTarget


class StoreValidatorTests(unittest.TestCase):
    def test_validate_openslo_payload(self):
        slo = SLO(
            name="latency-p95-checkout",
            service="checkout",
            target=SLOTarget(metric="latency_p95_ms", comparator="<=", threshold=200.0),
        )
        payload = export_open_slo([slo])
        ok, errors = validate_openslo_payload(payload)
        self.assertTrue(ok)
        self.assertEqual(errors, [])

    def test_store_roundtrip(self):
        store_path = ROOT / "tests" / "tmp_store.json"
        if store_path.exists():
            store_path.unlink()
        store = SLOStore(str(store_path))
        slo = SLO(
            name="availability-checkout",
            service="checkout",
            target=SLOTarget(metric="availability", comparator=">=", threshold=0.99),
        )
        store.save([slo], mode="replace")
        loaded = store.load_slos()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].name, slo.name)
        store_path.unlink()


if __name__ == "__main__":
    unittest.main()
