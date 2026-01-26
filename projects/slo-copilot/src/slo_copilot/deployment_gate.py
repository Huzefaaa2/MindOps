"""Deployment gate stub using emitted guardrail snippets."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .models import CopilotReport
from .trace_tests import metrics_from_stats
from .trace_stats import TraceStats


@dataclass
class GateDecision:
    passed: bool
    results: Dict[str, str]
    failures: List[str]


def evaluate_guardrails(policy_snippets: Dict[str, str], metrics: Dict[str, float]) -> GateDecision:
    results: Dict[str, str] = {}
    failures: List[str] = []
    for name, snippet in policy_snippets.items():
        try:
            exec(snippet, {}, {"metrics": metrics})
            results[name] = "pass"
        except Exception as exc:
            results[name] = f"fail: {exc}"
            failures.append(name)
    return GateDecision(passed=len(failures) == 0, results=results, failures=failures)


def gate_from_report(report: CopilotReport, stats: TraceStats) -> GateDecision:
    metrics_obj = metrics_from_stats(stats, report.coverage.coverage_ratio if report.coverage else None)
    metrics = {
        "latency_p50_ms": metrics_obj.latency_p50_ms,
        "latency_p95_ms": metrics_obj.latency_p95_ms,
        "latency_p99_ms": metrics_obj.latency_p99_ms,
        "error_rate": metrics_obj.error_rate,
        "availability": metrics_obj.availability,
        "coverage_ratio": metrics_obj.coverage_ratio,
    }
    return evaluate_guardrails(report.policy_snippets, metrics)
