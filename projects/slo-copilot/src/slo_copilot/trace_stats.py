"""Trace statistics and helpers for SLO Copilot."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional
import math

from .models import TraceSpan


@dataclass
class ServiceStats:
    span_count: int
    error_count: int
    error_rate: float
    latency_p50_ms: Optional[float]
    latency_p95_ms: Optional[float]
    latency_p99_ms: Optional[float]


@dataclass
class TraceStats:
    span_count: int
    error_count: int
    error_rate: float
    availability: float
    latency_p50_ms: Optional[float]
    latency_p95_ms: Optional[float]
    latency_p99_ms: Optional[float]
    service_stats: Dict[str, ServiceStats]


def _parse_numeric(value: object) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _parse_time(value: object) -> Optional[float]:
    numeric = _parse_numeric(value)
    if numeric is not None:
        return numeric
    if isinstance(value, str):
        try:
            normalized = value.replace("Z", "+00:00") if value.endswith("Z") else value
            dt = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    return None


def _duration_ms(start_time: object, end_time: object) -> Optional[float]:
    start = _parse_time(start_time)
    end = _parse_time(end_time)
    if start is None or end is None:
        return None

    # Heuristic scaling for epoch timestamps.
    scale = 1.0
    if start > 1e15 or end > 1e15:
        scale = 1e6  # nanoseconds to milliseconds
    elif start > 1e12 or end > 1e12:
        scale = 1e3  # microseconds to milliseconds
    elif start > 1e9 or end > 1e9:
        scale = 1e0  # seconds to milliseconds (seconds value)
        return max(0.0, (end - start) * 1000.0)

    return max(0.0, (end - start) / scale)


def _percentile(values: List[float], pct: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    k = (len(ordered) - 1) * pct
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return ordered[int(k)]
    return ordered[f] * (c - k) + ordered[c] * (k - f)


def _span_is_error(span: TraceSpan) -> bool:
    status = (span.status or "").upper()
    if status in {"ERROR", "STATUS_CODE_ERROR", "STATUS_CODE_UNKNOWN"}:
        return True
    status_code = span.attributes.get("http.status_code") or span.attributes.get("http.status")
    if isinstance(status_code, str) and status_code.isdigit():
        status_code = int(status_code)
    if isinstance(status_code, (int, float)) and status_code >= 500:
        return True
    if "exception.message" in span.attributes or "exception.type" in span.attributes:
        return True
    return False


def compute_trace_stats(spans: Iterable[TraceSpan]) -> TraceStats:
    latencies: List[float] = []
    error_count = 0
    service_latencies: Dict[str, List[float]] = {}
    service_errors: Dict[str, int] = {}
    service_counts: Dict[str, int] = {}

    span_list = list(spans)
    for span in span_list:
        duration = _duration_ms(span.start_time, span.end_time)
        if duration is not None:
            latencies.append(duration)
            service_latencies.setdefault(span.service_name, []).append(duration)
        service_counts[span.service_name] = service_counts.get(span.service_name, 0) + 1
        if _span_is_error(span):
            error_count += 1
            service_errors[span.service_name] = service_errors.get(span.service_name, 0) + 1

    span_count = len(span_list)
    error_rate = (error_count / span_count) if span_count else 0.0
    availability = 1.0 - error_rate

    latency_p50 = _percentile(latencies, 0.50)
    latency_p95 = _percentile(latencies, 0.95)
    latency_p99 = _percentile(latencies, 0.99)

    service_stats: Dict[str, ServiceStats] = {}
    for service, count in service_counts.items():
        service_latency = service_latencies.get(service, [])
        service_error_count = service_errors.get(service, 0)
        service_error_rate = (service_error_count / count) if count else 0.0
        service_stats[service] = ServiceStats(
            span_count=count,
            error_count=service_error_count,
            error_rate=service_error_rate,
            latency_p50_ms=_percentile(service_latency, 0.50),
            latency_p95_ms=_percentile(service_latency, 0.95),
            latency_p99_ms=_percentile(service_latency, 0.99),
        )

    return TraceStats(
        span_count=span_count,
        error_count=error_count,
        error_rate=error_rate,
        availability=availability,
        latency_p50_ms=latency_p50,
        latency_p95_ms=latency_p95,
        latency_p99_ms=latency_p99,
        service_stats=service_stats,
    )


def extract_observed_signals(spans: Iterable[TraceSpan]) -> List[str]:
    observed = []
    seen = set()
    for span in spans:
        op = span.operation or span.service_name
        if op and op not in seen:
            seen.add(op)
            observed.append(op)
    return observed
