"""Trace-based testing utilities."""
from __future__ import annotations

from typing import Iterable, List

from .evaluator import evaluate_slos
from .models import SLO, SLOEvaluation, SLOMetrics, TraceTestCase, TraceTestResult
from .trace_stats import TraceStats


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def metrics_from_stats(stats: TraceStats, coverage_ratio: float | None = None) -> SLOMetrics:
    return SLOMetrics(
        latency_p50_ms=stats.latency_p50_ms,
        latency_p95_ms=stats.latency_p95_ms,
        latency_p99_ms=stats.latency_p99_ms,
        error_rate=stats.error_rate,
        availability=stats.availability,
        coverage_ratio=coverage_ratio,
    )


def apply_faults(metrics: SLOMetrics, case: TraceTestCase) -> SLOMetrics:
    latency_p50 = metrics.latency_p50_ms
    latency_p95 = metrics.latency_p95_ms
    latency_p99 = metrics.latency_p99_ms
    if latency_p50 is not None:
        latency_p50 *= case.latency_multiplier
    if latency_p95 is not None:
        latency_p95 *= case.latency_multiplier
    if latency_p99 is not None:
        latency_p99 *= case.latency_multiplier

    error_rate = metrics.error_rate
    availability = metrics.availability
    if error_rate is not None:
        error_rate = _clamp(error_rate + case.error_rate_delta, 0.0, 1.0)
    if availability is not None:
        availability = _clamp(availability + case.availability_delta, 0.0, 1.0)

    return SLOMetrics(
        latency_p50_ms=latency_p50,
        latency_p95_ms=latency_p95,
        latency_p99_ms=latency_p99,
        error_rate=error_rate,
        availability=availability,
        coverage_ratio=metrics.coverage_ratio,
    )


class TraceTestRunner:
    def __init__(self) -> None:
        self.default_cases: List[TraceTestCase] = [
            TraceTestCase(
                name="baseline",
                description="Baseline trace replay without injected faults.",
            ),
            TraceTestCase(
                name="latency-spike",
                description="Increase latency across spans.",
                latency_multiplier=1.5,
            ),
            TraceTestCase(
                name="error-burst",
                description="Inject additional errors to stress the error budget.",
                error_rate_delta=0.05,
                availability_delta=-0.05,
            ),
            TraceTestCase(
                name="partial-outage",
                description="Simulate a partial availability drop.",
                error_rate_delta=0.1,
                availability_delta=-0.1,
            ),
        ]

    def run(self,
            slos: Iterable[SLO],
            stats: TraceStats,
            coverage_ratio: float | None = None,
            cases: Iterable[TraceTestCase] | None = None) -> List[TraceTestResult]:
        base_metrics = metrics_from_stats(stats, coverage_ratio)
        results: List[TraceTestResult] = []
        for case in cases or self.default_cases:
            mutated_metrics = apply_faults(base_metrics, case)
            evaluations: List[SLOEvaluation] = evaluate_slos(slos, mutated_metrics)
            results.append(TraceTestResult(case=case, evaluations=evaluations))
        return results
