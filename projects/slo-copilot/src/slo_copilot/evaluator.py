"""Evaluate SLOs against observed metrics."""
from __future__ import annotations

from typing import Iterable, List

from .models import SLO, SLOEvaluation, SLOMetrics


def _compare(observed: float, comparator: str, threshold: float) -> bool:
    if comparator == "<=" or comparator == "<":
        return observed <= threshold
    if comparator == ">=" or comparator == ">":
        return observed >= threshold
    if comparator == "==":
        return observed == threshold
    raise ValueError(f"Unsupported comparator: {comparator}")


def _metric_value(metrics: SLOMetrics, metric: str) -> float | None:
    return getattr(metrics, metric, None)


def evaluate_slo(slo: SLO, metrics: SLOMetrics) -> SLOEvaluation:
    observed = _metric_value(metrics, slo.target.metric)
    if observed is None:
        return SLOEvaluation(
            slo=slo,
            passed=False,
            observed_value=None,
            threshold=slo.target.threshold,
            comparator=slo.target.comparator,
            metric=slo.target.metric,
            details="Metric missing from evaluation context.",
        )
    passed = _compare(observed, slo.target.comparator, slo.target.threshold)
    detail = "meets objective" if passed else "violates objective"
    return SLOEvaluation(
        slo=slo,
        passed=passed,
        observed_value=round(observed, 4),
        threshold=slo.target.threshold,
        comparator=slo.target.comparator,
        metric=slo.target.metric,
        details=detail,
    )


def evaluate_slos(slos: Iterable[SLO], metrics: SLOMetrics) -> List[SLOEvaluation]:
    return [evaluate_slo(slo, metrics) for slo in slos]
