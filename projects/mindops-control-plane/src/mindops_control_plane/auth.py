"""Authn/authz stubs for the MindOps control plane."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

from fastapi import HTTPException, Request


@dataclass
class ActorContext:
    actor: str
    scopes: List[str]
    auth_mode: str


def _parse_scopes(raw: str | None) -> List[str]:
    if not raw:
        return []
    return [scope.strip() for scope in raw.split(",") if scope.strip()]


def require_auth(request: Request) -> ActorContext:
    """Require API key auth if CONTROL_PLANE_API_KEY is set."""
    api_key = os.getenv("CONTROL_PLANE_API_KEY")
    auth_header = request.headers.get("authorization", "")
    bearer = auth_header.replace("Bearer ", "").strip() if auth_header else ""
    provided = request.headers.get("x-api-key") or bearer

    if api_key:
        if not provided or provided != api_key:
            raise HTTPException(status_code=401, detail="Unauthorized")
        auth_mode = "api_key"
    else:
        auth_mode = "none"

    actor = request.headers.get("x-actor") or request.headers.get("x-user") or "anonymous"
    scopes = _parse_scopes(request.headers.get("x-scopes"))
    return ActorContext(actor=actor, scopes=scopes, auth_mode=auth_mode)


def authorize(actor: ActorContext, action: str) -> None:
    """Authorize an action (stub)."""
    mode = os.getenv("CONTROL_PLANE_AUTHZ_MODE", "allow-all")
    if mode == "deny-all":
        raise HTTPException(status_code=403, detail="Forbidden")
    if mode == "scoped" and actor.scopes and action not in actor.scopes:
        raise HTTPException(status_code=403, detail="Forbidden")
