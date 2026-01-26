"""Integration with Project 3 (eBPF Coverage Bot)."""
from __future__ import annotations

from typing import List, Optional

from .utils import IntegrationStatus, IntegrationUnavailable, ensure_project_path, optional_import
from ..models import CoverageReport


class EBPFCoverageAdapter:
    def __init__(self) -> None:
        ensure_project_path("ebpf-bot", "src")
        self._coverage_bot = optional_import("ebpf_bot.coverage_bot")
        self._orchestrator = optional_import("ebpf_bot.orchestrator")

    def analyze(self, expected_signals: List[str], observed_signals: Optional[List[str]] = None) -> CoverageReport:
        observed_signals = observed_signals or []
        bot = self._coverage_bot.CoverageBot(expected_signals)
        for signal in observed_signals:
            bot.observe(signal)
        coverage_map = bot.get_coverage()
        score = bot.coverage_score()
        missing = bot.find_missing_signals(observed_signals)
        suggestions = bot.suggest_instrumentation(missing)
        next_probe = None
        if coverage_map:
            orchestrator = self._orchestrator.CoverageOrchestrator()
            next_probe = orchestrator.decide_next_probe(coverage_map)
        return CoverageReport(
            expected_signals=expected_signals,
            observed_signals=observed_signals,
            coverage_map=coverage_map,
            coverage_ratio=score,
            missing_signals=missing,
            next_probe=next_probe,
            suggestions=suggestions,
        )


def ebpf_status() -> IntegrationStatus:
    try:
        ensure_project_path("ebpf-bot", "src")
        optional_import("ebpf_bot.coverage_bot")
        return IntegrationStatus(name="ebpf-bot", status="ready")
    except IntegrationUnavailable as exc:
        return IntegrationStatus(name="ebpf-bot", status="unavailable", detail=str(exc))
