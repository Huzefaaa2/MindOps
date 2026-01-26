"""Stub integration for Project 7 (Topology Graph RCA)."""
from __future__ import annotations

from typing import Dict


class TopologyRcaAdapter:
    def status(self) -> Dict[str, str]:
        return {"status": "not_configured", "detail": "Topology RCA pending Project 7."}

    def analyze(self, service_name: str) -> Dict[str, str]:
        return {"status": "not_configured", "detail": "Graph RCA will be wired in Project 7."}
