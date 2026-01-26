"""Telemetry policy helpers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


ACTION_TO_RATE = {
    "decrease_sampling": 0.2,
    "maintain_sampling": 0.5,
    "increase_sampling": 1.0,
}


def load_sampling_policy(path: str) -> Optional[float]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        rate = data.get("sampling_rate")
        if isinstance(rate, (int, float)):
            return float(rate)
        action = data.get("sampling_action") or data.get("action")
        if isinstance(action, str):
            return ACTION_TO_RATE.get(action)
    return None
