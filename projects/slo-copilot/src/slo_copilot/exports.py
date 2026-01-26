"""Export helpers for SLO Copilot."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Iterable, List, Set

from .models import SLO


def export_slo_json(slos: Iterable[SLO]) -> Dict[str, object]:
    return {
        "schema_version": "slo-copilot/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "slos": [
            {
                "name": slo.name,
                "service": slo.service,
                "description": slo.description,
                "labels": slo.labels,
                "target": {
                    "metric": slo.target.metric,
                    "comparator": slo.target.comparator,
                    "threshold": slo.target.threshold,
                    "window_days": slo.target.window_days,
                },
            }
            for slo in slos
        ],
    }


def export_open_slo(slos: Iterable[SLO]) -> List[Dict[str, object]]:
    slo_list = list(slos)
    resources: List[Dict[str, object]] = []
    resources.extend(_service_resources(slo_list))
    resources.extend(_sli_resources(slo_list))
    resources.extend(_slo_resources(slo_list))
    return resources


def _service_resources(slos: Iterable[SLO]) -> List[Dict[str, object]]:
    seen: Set[str] = set()
    services: List[Dict[str, object]] = []
    for slo in slos:
        if slo.service in seen:
            continue
        seen.add(slo.service)
        services.append(
            {
                "apiVersion": "openslo/v1",
                "kind": "Service",
                "metadata": {"name": slo.service},
                "spec": {
                    "description": f"Service for {slo.service}",
                },
            }
        )
    return services


def _sli_resources(slos: Iterable[SLO]) -> List[Dict[str, object]]:
    slis: List[Dict[str, object]] = []
    for slo in slos:
        slis.append(
            {
                "apiVersion": "openslo/v1",
                "kind": "SLI",
                "metadata": {"name": f"{slo.name}-sli", "labels": slo.labels},
                "spec": {
                    "service": slo.service,
                    "indicator": {
                        "type": "metric",
                        "metricSource": "trace-derived",
                        "metric": slo.target.metric,
                    },
                },
            }
        )
    return slis


def _slo_resources(slos: Iterable[SLO]) -> List[Dict[str, object]]:
    resources: List[Dict[str, object]] = []
    for slo in slos:
        resources.append(
            {
                "apiVersion": "openslo/v1",
                "kind": "SLO",
                "metadata": {
                    "name": slo.name,
                    "labels": slo.labels,
                },
                "spec": {
                    "description": slo.description,
                    "service": slo.service,
                    "indicator": {
                        "type": "metric",
                        "metricSource": "trace-derived",
                        "metric": slo.target.metric,
                    },
                    "objectives": [
                        {
                            "displayName": slo.name,
                            "op": slo.target.comparator,
                            "value": slo.target.threshold,
                            "timeWindow": {
                                "count": slo.target.window_days,
                                "unit": "Day",
                            },
                        }
                    ],
                },
            }
        )
    return resources
