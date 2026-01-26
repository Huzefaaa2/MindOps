"""PII detection patterns and helpers."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, List, Optional, Pattern


@dataclass
class PatternRule:
    label: str
    regex: Pattern[str]
    validator: Optional[Callable[[str], bool]] = None


EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b")
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
CREDIT_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")

API_KEY_RE = re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")


def _luhn_valid(candidate: str) -> bool:
    digits = [int(ch) for ch in re.sub(r"\D", "", candidate)]
    if len(digits) < 13:
        return False
    checksum = 0
    parity = len(digits) % 2
    for idx, digit in enumerate(digits):
        if idx % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


def _is_ipv4(candidate: str) -> bool:
    parts = candidate.split(".")
    if len(parts) != 4:
        return False
    for part in parts:
        try:
            value = int(part)
        except ValueError:
            return False
        if value < 0 or value > 255:
            return False
    return True


DEFAULT_RULES: List[PatternRule] = [
    PatternRule(label="email", regex=EMAIL_RE),
    PatternRule(label="ssn", regex=SSN_RE),
    PatternRule(label="phone", regex=PHONE_RE),
    PatternRule(label="ipv4", regex=IPV4_RE, validator=_is_ipv4),
    PatternRule(label="credit_card", regex=CREDIT_CARD_RE, validator=_luhn_valid),
    PatternRule(label="api_key", regex=API_KEY_RE),
]
