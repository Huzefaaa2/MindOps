"""Audit logging stub for control plane actions."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .auth import ActorContext


AUDIT_LOG = Path(
    os.getenv(
        "CONTROL_PLANE_AUDIT_LOG",
        str(Path(__file__).resolve().parents[2] / "data" / "audit.log"),
    )
)


def audit_event(
    action: str,
    actor: ActorContext,
    status: str = "ok",
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Write a JSONL audit record (best-effort)."""
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "actor": actor.actor,
        "auth_mode": actor.auth_mode,
        "status": status,
        "details": details or {},
    }

    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT_LOG.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True))
            handle.write("\n")
    except Exception:
        # Swallow audit errors in this lightweight stub.
        return
