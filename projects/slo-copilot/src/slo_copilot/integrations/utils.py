"""Helpers for optional integrations."""
from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
import sys
from types import ModuleType
from typing import Optional


class IntegrationUnavailable(RuntimeError):
    """Raised when an optional integration cannot be loaded."""


@dataclass
class IntegrationStatus:
    name: str
    status: str
    detail: str = ""


def find_repo_root(start: Optional[Path] = None) -> Optional[Path]:
    origin = start or Path(__file__).resolve()
    for parent in [origin] + list(origin.parents):
        if (parent / "projects").is_dir():
            return parent
    return None


def add_sys_path(path: Path) -> None:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def ensure_project_path(project_name: str, src_subpath: Optional[str] = None) -> Path:
    repo_root = find_repo_root()
    if repo_root is None:
        raise IntegrationUnavailable("Unable to locate repo root with projects directory.")
    project_path = repo_root / "projects" / project_name
    if src_subpath:
        project_path = project_path / src_subpath
    if not project_path.exists():
        raise IntegrationUnavailable(f"Project path missing: {project_path}")
    add_sys_path(project_path)
    return project_path


def optional_import(module_name: str) -> ModuleType:
    try:
        return import_module(module_name)
    except Exception as exc:  # pragma: no cover - surfaced in integration status
        raise IntegrationUnavailable(f"Failed to import {module_name}: {exc}") from exc
