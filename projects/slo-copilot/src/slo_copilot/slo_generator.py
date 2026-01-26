"""SLO generation heuristics for SLO Copilot."""
from __future__ import annotations

from typing import List, Optional

from .models import CoverageReport, SLO, SLOTarget
from .trace_stats import TraceStats, ServiceStats


class SLOGenerator:
    """Generate candidate SLOs from trace statistics and coverage data."""

    def __init__(self, window_days: int = 30) -> None:
        self.window_days = window_days

    def generate(self, stats: TraceStats, coverage: Optional[CoverageReport] = None) -> List[SLO]:
        slos: List[SLO] = []
        for service_name, service_stats in stats.service_stats.items():
            slos.extend(self._slos_for_service(service_name, service_stats))

        if coverage:
            slos.append(
                SLO(
                    name=f"telemetry-coverage-{coverage.expected_signals[0] if coverage.expected_signals else 'signals'}",
                    service="telemetry",
                    target=SLOTarget(
                        metric="coverage_ratio",
                        comparator=">=",
                        threshold=max(0.9, coverage.coverage_ratio),
                        window_days=self.window_days,
                    ),
                    description="Maintain high coverage of expected probes for trace-based testing.",
                    labels={"source": "ebpf-bot"},
                )
            )
        return slos

    def _slos_for_service(self, service_name: str, service_stats: ServiceStats) -> List[SLO]:
        slos: List[SLO] = []
        if service_stats.latency_p95_ms is not None:
            latency_threshold = max(150.0, service_stats.latency_p95_ms * 1.25)
            slos.append(
                SLO(
                    name=f"latency-p95-{service_name}",
                    service=service_name,
                    target=SLOTarget(
                        metric="latency_p95_ms",
                        comparator="<=",
                        threshold=round(latency_threshold, 2),
                        window_days=self.window_days,
                    ),
                    description="p95 latency stays within a safe envelope.",
                    labels={"sli": "latency"},
                )
            )
        error_budget = max(0.001, service_stats.error_rate * 0.5)
        slos.append(
            SLO(
                name=f"error-rate-{service_name}",
                service=service_name,
                target=SLOTarget(
                    metric="error_rate",
                    comparator="<=",
                    threshold=round(error_budget, 4),
                    window_days=self.window_days,
                ),
                description="Error rate remains within the allocated error budget.",
                labels={"sli": "errors"},
            )
        )

        availability_target = max(0.99, 1.0 - error_budget)
        slos.append(
            SLO(
                name=f"availability-{service_name}",
                service=service_name,
                target=SLOTarget(
                    metric="availability",
                    comparator=">=",
                    threshold=round(availability_target, 4),
                    window_days=self.window_days,
                ),
                description="Availability stays above the reliability target.",
                labels={"sli": "availability"},
            )
        )
        return slos
