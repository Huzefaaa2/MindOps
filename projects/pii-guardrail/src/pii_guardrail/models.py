"""Data models for PII Guardrail."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class RedactionMatch:
    label: str
    value: str
    start: int
    end: int


@dataclass
class RedactionResult:
    original: str
    redacted: str
    matches: List[RedactionMatch] = field(default_factory=list)


@dataclass
class ScrubReport:
    total_fields: int
    total_redactions: int
    by_label: Dict[str, int]
