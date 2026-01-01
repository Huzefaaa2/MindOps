"""eBPF Coverage Bot module.

This module provides a CoverageBot class that identifies observability
blind spots by comparing expected telemetry signals (metrics, traces)
against what is actually collected. It can suggest or insert eBPF 
instrumentation to cover missing telemetry.
"""
from typing import List

class CoverageBot:
    """Monitors telemetry coverage and suggests additional instrumentation for blind spots."""

    def __init__(self, expected_signals: List[str]) -> None:
        """Initialize the CoverageBot with a list of expected telemetry signals."""
        self.expected_signals = expected_signals

    def find_missing_signals(self, observed_signals: List[str]) -> List[str]:
        """Return a list of signals that are expected but not observed."""
        missing = [sig for sig in self.expected_signals if sig not in observed_signals]
        return missing

    def suggest_instrumentation(self, missing_signals: List[str]) -> List[str]:
        """Generate suggestions for instrumentation (e.g., eBPF probes) for each missing signal."""
        suggestions = []
        for sig in missing_signals:
            suggestions.append(f"Add eBPF probe for '{sig}'")
        return suggestions
