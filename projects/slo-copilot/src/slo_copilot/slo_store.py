"""Persistent SLO store for SLO Copilot."""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from .exports import export_slo_json
from .models import SLO, SLOTarget


class SLOStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def load_raw(self) -> Dict[str, object]:
        if not self.path.exists():
            return {"schema_version": "slo-store/v1", "slos": []}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def load_slos(self) -> List[SLO]:
        data = self.load_raw()
        slos = []
        for item in data.get("slos", []):
            slos.append(_slo_from_dict(item))
        return slos

    def save(self, slos: List[SLO], mode: str = "merge") -> Dict[str, object]:
        if mode not in {"merge", "replace"}:
            raise ValueError("mode must be 'merge' or 'replace'")
        if mode == "merge" and self.path.exists():
            existing = self.load_slos()
            by_key = {(slo.service, slo.name): slo for slo in existing}
            for slo in slos:
                by_key[(slo.service, slo.name)] = slo
            merged = list(by_key.values())
        else:
            merged = slos
        payload = export_slo_json(merged)
        payload["store_version"] = "slo-store/v1"
        payload["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload


def _slo_from_dict(data: Dict[str, object]) -> SLO:
    target = data.get("target", {}) if isinstance(data.get("target"), dict) else {}
    return SLO(
        name=str(data.get("name", "unknown")),
        service=str(data.get("service", "unknown")),
        target=SLOTarget(
            metric=str(target.get("metric", "unknown")),
            comparator=str(target.get("comparator", ">=")),
            threshold=float(target.get("threshold", 0.0)),
            window_days=int(target.get("window_days", 30)),
        ),
        description=str(data.get("description", "")),
        labels=data.get("labels", {}) if isinstance(data.get("labels"), dict) else {},
    )
