"""PII scrubbing utilities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple, Union

from .models import RedactionMatch, RedactionResult, ScrubReport
from .patterns import DEFAULT_RULES, PatternRule


@dataclass
class ScrubberConfig:
    redaction_token: str = "[REDACTED]"
    enabled_labels: List[str] | None = None


class PIIScrubber:
    def __init__(self, config: ScrubberConfig | None = None, rules: List[PatternRule] | None = None) -> None:
        self.config = config or ScrubberConfig()
        self.rules = rules or DEFAULT_RULES

    def scrub_text(self, text: str) -> RedactionResult:
        matches: List[RedactionMatch] = []
        redacted = text
        offset = 0
        for rule in self._active_rules():
            for match in rule.regex.finditer(text):
                value = match.group(0)
                if rule.validator and not rule.validator(value):
                    continue
                start = match.start()
                end = match.end()
                matches.append(RedactionMatch(label=rule.label, value=value, start=start, end=end))
        # Apply replacements in reverse order to keep indices stable
        for match in sorted(matches, key=lambda m: m.start, reverse=True):
            redacted = redacted[:match.start] + self.config.redaction_token + redacted[match.end:]
        return RedactionResult(original=text, redacted=redacted, matches=matches)

    def scrub_object(self, obj: object) -> Tuple[object, ScrubReport, List[RedactionMatch]]:
        redactions: List[RedactionMatch] = []
        total_fields = 0

        def _scrub(value: object) -> object:
            nonlocal total_fields
            if isinstance(value, str):
                total_fields += 1
                result = self.scrub_text(value)
                redactions.extend(result.matches)
                return result.redacted
            if isinstance(value, list):
                return [_scrub(item) for item in value]
            if isinstance(value, dict):
                return {key: _scrub(val) for key, val in value.items()}
            return value

        redacted_obj = _scrub(obj)
        report = _build_report(total_fields, redactions)
        return redacted_obj, report, redactions

    def scrub_records(self, records: Iterable[object]) -> Tuple[List[object], ScrubReport]:
        redactions: List[RedactionMatch] = []
        total_fields = 0
        results: List[object] = []
        for record in records:
            redacted, report, matches = self.scrub_object(record)
            results.append(redacted)
            total_fields += report.total_fields
            redactions.extend(matches)
        report = _build_report(total_fields, redactions)
        return results, report

    def _active_rules(self) -> List[PatternRule]:
        if not self.config.enabled_labels:
            return self.rules
        labels = set(self.config.enabled_labels)
        return [rule for rule in self.rules if rule.label in labels]


def _build_report(total_fields: int, redactions: List[RedactionMatch]) -> ScrubReport:
    by_label: Dict[str, int] = {}
    for match in redactions:
        by_label[match.label] = by_label.get(match.label, 0) + 1
    return ScrubReport(
        total_fields=total_fields,
        total_redactions=len(redactions),
        by_label=by_label,
    )

