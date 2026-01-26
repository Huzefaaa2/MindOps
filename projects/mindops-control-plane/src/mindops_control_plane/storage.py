"""Simple JSON storage for control plane state."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def load_state(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"sampling_policy": {"sampling_action": "maintain_sampling"}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: Dict[str, Any]) -> Dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state
