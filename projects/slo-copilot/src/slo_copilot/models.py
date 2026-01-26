"""Core data models for SLO Copilot."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TraceSpan:
    trace_id: str
    span_id: str
    parent_id: Optional[str]
    service_name: str
    operation: str
    start_time: Any
    end_time: Any
    attributes: Dict[str, Any]
    status: str


@dataclass
class SLOTarget:
    metric: str
    comparator: str
    threshold: float
    window_days: int = 30


@dataclass
class SLO:
    name: str
    service: str
    target: SLOTarget
    description: str = ""
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class SLOMetrics:
    latency_p50_ms: Optional[float] = None
    latency_p95_ms: Optional[float] = None
    latency_p99_ms: Optional[float] = None
    error_rate: Optional[float] = None
    availability: Optional[float] = None
    coverage_ratio: Optional[float] = None


@dataclass
class SLOEvaluation:
    slo: SLO
    passed: bool
    observed_value: Optional[float]
    threshold: float
    comparator: str
    metric: str
    details: str = ""


@dataclass
class CoverageReport:
    expected_signals: List[str]
    observed_signals: List[str]
    coverage_map: Dict[str, bool]
    coverage_ratio: float
    missing_signals: List[str]
    next_probe: Optional[str]
    suggestions: List[str]


@dataclass
class TelemetryRecommendation:
    sampling_action: str
    budget_alert: bool
    forecast: List[float]
    notes: List[str] = field(default_factory=list)


@dataclass
class TraceTestCase:
    name: str
    description: str
    latency_multiplier: float = 1.0
    error_rate_delta: float = 0.0
    availability_delta: float = 0.0


@dataclass
class TraceTestResult:
    case: TraceTestCase
    evaluations: List[SLOEvaluation]


@dataclass
class CopilotReport:
    slo_candidates: List[SLO]
    baseline_evaluations: List[SLOEvaluation]
    test_results: List[TraceTestResult]
    coverage: Optional[CoverageReport]
    telemetry_recommendation: Optional[TelemetryRecommendation]
    rca: Optional[Dict[str, Any]]
    policy_snippets: Dict[str, str]
    integrations: Dict[str, Dict[str, Any]]
    future_integrations: Dict[str, Dict[str, Any]]
