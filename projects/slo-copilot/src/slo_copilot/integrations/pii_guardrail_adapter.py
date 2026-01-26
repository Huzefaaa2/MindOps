"""Integration for Project 6 (PII Guardrail)."""
from __future__ import annotations

from typing import Dict, List

from ..models import TraceSpan
from .utils import IntegrationUnavailable, ensure_project_path, optional_import


class PiiGuardrailAdapter:
    def __init__(self) -> None:
        ensure_project_path("pii-guardrail", "src")
        self._scrubber = optional_import("pii_guardrail.scrubber")

    def status(self) -> Dict[str, str]:
        try:
            ensure_project_path("pii-guardrail", "src")
            optional_import("pii_guardrail.scrubber")
            return {"status": "ready", "detail": "PII Guardrail available."}
        except IntegrationUnavailable as exc:
            return {"status": "unavailable", "detail": str(exc)}

    def scrub(self, spans: List[TraceSpan]) -> List[TraceSpan]:
        try:
            scrubber = self._scrubber.PIIScrubber()
        except Exception:
            return spans
        payload = [span.__dict__ for span in spans]
        redacted, _report, _matches = scrubber.scrub_object(payload)
        return [TraceSpan(**item) for item in redacted]
