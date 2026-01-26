"""Integration with Project 2 (T-RAG)."""
from __future__ import annotations

from typing import List

from .utils import IntegrationStatus, IntegrationUnavailable, ensure_project_path, optional_import
from ..models import TraceSpan


class TragTraceAdapter:
    def __init__(self) -> None:
        ensure_project_path("t-rag", "src")
        self._trace_loader = optional_import("t_rag.trace_loader")

    def load_spans(self, trace_path: str) -> List[TraceSpan]:
        loader = self._trace_loader.TraceLoader(trace_path)
        records = loader.load_spans()
        return [
            TraceSpan(
                trace_id=rec.trace_id,
                span_id=rec.span_id,
                parent_id=rec.parent_id,
                service_name=rec.service_name,
                operation=rec.operation,
                start_time=rec.start_time,
                end_time=rec.end_time,
                attributes=rec.attributes,
                status=str(rec.status),
            )
            for rec in records
        ]


class TragRcaAdapter:
    def __init__(self) -> None:
        ensure_project_path("t-rag", "src")
        self._service = optional_import("t_rag.service")

    def analyze(self, trace_path: str) -> dict:
        return self._service.run(trace_path)


def trag_status() -> IntegrationStatus:
    try:
        ensure_project_path("t-rag", "src")
        optional_import("t_rag.trace_loader")
        return IntegrationStatus(name="t-rag", status="ready")
    except IntegrationUnavailable as exc:
        return IntegrationStatus(name="t-rag", status="unavailable", detail=str(exc))
