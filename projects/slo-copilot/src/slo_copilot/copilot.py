"""Orchestrator for SLO Copilot."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .evaluator import evaluate_slos
from .models import (
    CopilotReport,
    CoverageReport,
    SLO,
    SLOEvaluation,
    TelemetryRecommendation,
    TraceSpan,
    TraceTestResult,
)
from .policy_emitter import emit_policy_bundle
from .slo_generator import SLOGenerator
from .trace_stats import TraceStats, compute_trace_stats, extract_observed_signals
from .trace_tests import TraceTestRunner, metrics_from_stats
from .integrations import (
    CAATAdapter,
    EBPFCoverageAdapter,
    PiiGuardrailAdapter,
    TopologyRcaAdapter,
    TragRcaAdapter,
    TragTraceAdapter,
    ZeroTouchTelemetryAdapter,
    IntegrationUnavailable,
    caat_status,
    ebpf_status,
    trag_status,
)


class SLOCopilot:
    def __init__(
        self,
        enable_caat: bool = True,
        enable_trag: bool = True,
        enable_ebpf: bool = True,
        zero_touch: Optional[ZeroTouchTelemetryAdapter] = None,
        pii_guardrail: Optional[PiiGuardrailAdapter] = None,
        topology_rca: Optional[TopologyRcaAdapter] = None,
    ) -> None:
        self.enable_caat = enable_caat
        self.enable_trag = enable_trag
        self.enable_ebpf = enable_ebpf
        self.zero_touch = zero_touch or ZeroTouchTelemetryAdapter()
        self.pii_guardrail = pii_guardrail or PiiGuardrailAdapter()
        self.topology_rca = topology_rca or TopologyRcaAdapter()
        self.generator = SLOGenerator()
        self.tester = TraceTestRunner()

    def run(
        self,
        trace_path: str,
        telemetry_volumes: Optional[List[float]] = None,
        expected_signals: Optional[List[str]] = None,
        observed_signals: Optional[List[str]] = None,
    ) -> CopilotReport:
        spans = self._load_spans(trace_path)
        spans = self.pii_guardrail.scrub(spans)
        stats = compute_trace_stats(spans)

        observed_signals = observed_signals or extract_observed_signals(spans)
        coverage_report = self._coverage(expected_signals, observed_signals)

        slos = self.generator.generate(stats, coverage_report)
        base_metrics = metrics_from_stats(stats, coverage_report.coverage_ratio if coverage_report else None)
        baseline_evaluations = evaluate_slos(slos, base_metrics)

        test_results = self.tester.run(slos, stats, coverage_report.coverage_ratio if coverage_report else None)
        rca_result = self._rca(trace_path, baseline_evaluations, test_results)

        telemetry_recommendation = self._telemetry_recommendation(stats, telemetry_volumes)
        policy_snippets = emit_policy_bundle(slos)

        integrations = {
            "caat": caat_status().__dict__,
            "t-rag": trag_status().__dict__,
            "ebpf-bot": ebpf_status().__dict__,
            "pii-guardrail": self.pii_guardrail.status(),
        }

        future_integrations = {
            "zero_touch_telemetry": self.zero_touch.status(),
            "topology_rca": self.topology_rca.status(),
        }

        return CopilotReport(
            slo_candidates=slos,
            baseline_evaluations=baseline_evaluations,
            test_results=test_results,
            coverage=coverage_report,
            telemetry_recommendation=telemetry_recommendation,
            rca=rca_result,
            policy_snippets=policy_snippets,
            integrations=integrations,
            future_integrations=future_integrations,
        )

    def _load_spans(self, trace_path: str) -> List[TraceSpan]:
        if self.enable_trag:
            try:
                adapter = TragTraceAdapter()
                return adapter.load_spans(trace_path)
            except IntegrationUnavailable:
                pass
        return self._load_spans_fallback(trace_path)

    def _load_spans_fallback(self, trace_path: str) -> List[TraceSpan]:
        data = json.loads(Path(trace_path).read_text(encoding="utf-8"))
        spans: List[Dict[str, Any]]
        if isinstance(data, list):
            spans = data
        else:
            spans = []
            for resource in data.get("resourceSpans", []):
                for scope in resource.get("scopeSpans", []):
                    spans.extend(scope.get("spans", []))
        results: List[TraceSpan] = []
        for span in spans:
            attrs = {}
            for attribute in span.get("attributes", []):
                key = attribute.get("key") or attribute.get("name")
                value = attribute.get("value")
                if isinstance(value, dict):
                    value = next(iter(value.values()))
                attrs[key] = value
            results.append(
                TraceSpan(
                    trace_id=span.get("traceId") or span.get("trace_id") or "unknown",
                    span_id=span.get("spanId") or span.get("span_id") or "unknown",
                    parent_id=span.get("parentSpanId") or span.get("parent_id"),
                    service_name=_extract_service_name(span) or "unknown_service",
                    operation=span.get("name") or span.get("operationName") or "unknown_operation",
                    start_time=span.get("startTimeUnixNano") or span.get("startTime"),
                    end_time=span.get("endTimeUnixNano") or span.get("endTime"),
                    attributes=attrs,
                    status=_extract_status(span),
                )
            )
        return results

    def _coverage(self,
                  expected_signals: Optional[List[str]],
                  observed_signals: Optional[List[str]]) -> Optional[CoverageReport]:
        if not self.enable_ebpf:
            return None
        if not expected_signals:
            expected_signals = ["probe_a", "probe_b", "probe_c"]
        observed_signals = observed_signals or []
        try:
            adapter = EBPFCoverageAdapter()
            return adapter.analyze(expected_signals, observed_signals)
        except IntegrationUnavailable:
            return None

    def _rca(self,
             trace_path: str,
             baseline_evaluations: List[SLOEvaluation],
             test_results: List[TraceTestResult]) -> Optional[Dict[str, Any]]:
        if not self.enable_trag:
            return None
        violation = any(not eval_item.passed for eval_item in baseline_evaluations)
        violation = violation or any(
            not evaluation.passed
            for result in test_results
            for evaluation in result.evaluations
        )
        if not violation:
            return None
        try:
            adapter = TragRcaAdapter()
            return adapter.analyze(trace_path)
        except IntegrationUnavailable:
            return None

    def _telemetry_recommendation(self,
                                  stats: TraceStats,
                                  telemetry_volumes: Optional[List[float]]) -> Optional[TelemetryRecommendation]:
        if not self.enable_caat:
            return None
        try:
            adapter = CAATAdapter()
            return adapter.recommend(
                telemetry_volumes=telemetry_volumes,
                anomaly_flag=stats.error_rate > 0.0,
                current_relative_cost=None,
            )
        except IntegrationUnavailable:
            return None


def _extract_service_name(span: Dict[str, Any]) -> Optional[str]:
    for attribute in span.get("attributes", []):
        key = attribute.get("key") or attribute.get("name")
        if key == "service.name":
            value = attribute.get("value")
            if isinstance(value, dict):
                value = value.get("stringValue") or value.get("value")
            return value
    resource = span.get("resource") or {}
    for attribute in resource.get("attributes", []):
        key = attribute.get("key") or attribute.get("name")
        if key == "service.name":
            value = attribute.get("value")
            if isinstance(value, dict):
                value = value.get("stringValue") or value.get("value")
            return value
    return None


def _extract_status(span: Dict[str, Any]) -> str:
    status = span.get("status", {})
    return status.get("message") or status.get("code") or "OK"
