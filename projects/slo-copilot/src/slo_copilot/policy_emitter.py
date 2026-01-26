"""Emit enforcement snippets for SLOs."""
from __future__ import annotations

from typing import Dict, Iterable

from .models import SLO


def emit_policy_snippet(slo: SLO) -> str:
    metric = slo.target.metric
    comparator = slo.target.comparator
    threshold = slo.target.threshold
    return (
        f"# Guardrail for {slo.service} / {slo.name}\n"
        f"if metrics['{metric}'] {comparator} {threshold}:\n"
        "    pass\n"
        "else:\n"
        f"    raise RuntimeError('SLO violation: {slo.name}')\n"
    )


def emit_policy_bundle(slos: Iterable[SLO]) -> Dict[str, str]:
    return {slo.name: emit_policy_snippet(slo) for slo in slos}
