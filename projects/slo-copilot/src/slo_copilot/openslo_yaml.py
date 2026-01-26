"""OpenSLO YAML exporter for SLO Copilot."""
from __future__ import annotations

import json
from typing import Any, Iterable

from .exports import export_open_slo
from .models import SLO


def export_open_slo_yaml(slos: Iterable[SLO]) -> str:
    """Emit a simple YAML representation of OpenSLO resources.

    The output is a YAML stream (documents separated by ---). It is a
    minimal serializer designed for simple string values, lists, and
    dicts produced by `export_open_slo`.
    """
    resources = export_open_slo(slos)
    return "\n".join(_to_yaml(resource) for resource in resources)


def _to_yaml(data: Any, indent: int = 0) -> str:
    spacer = "  " * indent
    if isinstance(data, dict):
        lines = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{spacer}{key}:")
                lines.append(_to_yaml(value, indent + 1))
            else:
                lines.append(f"{spacer}{key}: {_scalar(value)}")
        return "\n".join(lines)
    if isinstance(data, list):
        lines = []
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(f"{spacer}-")
                lines.append(_to_yaml(item, indent + 1))
            else:
                lines.append(f"{spacer}- {_scalar(item)}")
        return "\n".join(lines)
    return f"{spacer}{_scalar(data)}"


def _scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if _needs_quotes(text):
        return json.dumps(text)
    return text


def _needs_quotes(text: str) -> bool:
    return (
        text == ""
        or text.strip() != text
        or ":" in text
        or "#" in text
        or "\n" in text
        or text.lower() in {"null", "true", "false"}
    )
