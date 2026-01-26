"""Language detection heuristics for container images."""
from __future__ import annotations

from typing import Dict


LANGUAGE_HINTS: Dict[str, str] = {
    "python": "python",
    "py": "python",
    "django": "python",
    "flask": "python",
    "fastapi": "python",
    "node": "nodejs",
    "nodejs": "nodejs",
    "npm": "nodejs",
    "yarn": "nodejs",
    "java": "java",
    "jre": "java",
    "jvm": "java",
    "spring": "java",
    "golang": "go",
    "go": "go",
    "dotnet": "dotnet",
    "aspnet": "dotnet",
    "ruby": "ruby",
    "rails": "ruby",
}


def detect_language(image: str, labels: Dict[str, str] | None = None) -> str:
    labels = labels or {}
    label_hint = labels.get("telemetry.mindops/language")
    if label_hint:
        return label_hint
    lowered = image.lower()
    for token, language in LANGUAGE_HINTS.items():
        if token in lowered:
            return language
    return "unknown"
