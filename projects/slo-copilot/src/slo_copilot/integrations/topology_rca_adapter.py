"""Integration for Project 7 (Topology Graph RCA)."""
from __future__ import annotations

from typing import Dict, List, Optional

from .utils import IntegrationUnavailable, ensure_project_path, optional_import

class TopologyRcaAdapter:
    def __init__(self) -> None:
        ensure_project_path("topology-graph-rca", "src")
        self._analyzer = optional_import("topology_graph_rca.analyzer")

    def status(self) -> Dict[str, str]:
        try:
            ensure_project_path("topology-graph-rca", "src")
            optional_import("topology_graph_rca.analyzer")
            return {"status": "ready", "detail": "Topology Graph RCA available."}
        except IntegrationUnavailable as exc:
            return {"status": "unavailable", "detail": str(exc)}

    def analyze(self, manifest_paths: Optional[List[str]] = None, trace_paths: Optional[List[str]] = None) -> Dict[str, object]:
        analyzer = self._analyzer.TopologyAnalyzer()
        report = analyzer.analyze(manifest_paths=manifest_paths, trace_paths=trace_paths)
        return report.__dict__
