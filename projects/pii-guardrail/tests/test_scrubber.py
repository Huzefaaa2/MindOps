import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pii_guardrail.scrubber import PIIScrubber, ScrubberConfig


class ScrubberTests(unittest.TestCase):
    def test_scrub_text(self):
        scrubber = PIIScrubber()
        text = "Email alice@example.com and SSN 123-45-6789"
        result = scrubber.scrub_text(text)
        self.assertIn("[REDACTED]", result.redacted)
        labels = {m.label for m in result.matches}
        self.assertIn("email", labels)
        self.assertIn("ssn", labels)

    def test_enabled_labels(self):
        scrubber = PIIScrubber(config=ScrubberConfig(enabled_labels=["email"]))
        text = "Email alice@example.com and SSN 123-45-6789"
        result = scrubber.scrub_text(text)
        labels = {m.label for m in result.matches}
        self.assertIn("email", labels)
        self.assertNotIn("ssn", labels)

    def test_scrub_object(self):
        scrubber = PIIScrubber()
        payload = {"user": {"email": "alice@example.com", "ip": "192.168.0.1"}}
        redacted, report, _matches = scrubber.scrub_object(payload)
        self.assertIn("[REDACTED]", redacted["user"]["email"])
        self.assertGreaterEqual(report.total_redactions, 1)


if __name__ == "__main__":
    unittest.main()
