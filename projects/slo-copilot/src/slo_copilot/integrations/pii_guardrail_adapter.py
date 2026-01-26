"""Stub integration for Project 6 (PII Guardrail)."""
from __future__ import annotations

from typing import Dict, List

from ..models import TraceSpan


class PiiGuardrailAdapter:
    def status(self) -> Dict[str, str]:
        return {"status": "not_configured", "detail": "PII redaction pending Project 6."}

    def scrub(self, spans: List[TraceSpan]) -> List[TraceSpan]:
        return spans
