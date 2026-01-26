"""MindOps Control Plane API."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from .audit import audit_event
from .auth import ActorContext, authorize, require_auth
from .storage import load_state, save_state

app = FastAPI(title="MindOps Control Plane", version="0.1.0")

REPO_ROOT = Path(__file__).resolve()
for parent in [REPO_ROOT] + list(REPO_ROOT.parents):
    if (parent / "projects").is_dir():
        REPO_ROOT = parent
        break

CONTROL_STORE = Path(os.getenv("CONTROL_PLANE_STORE", str(REPO_ROOT / "projects" / "mindops-control-plane" / "data" / "control_plane_state.json")))
SLO_STORE = Path(os.getenv("SLO_STORE_PATH", str(REPO_ROOT / "projects" / "slo-copilot" / "data" / "slo_store.json")))


def _extend_path(path: Path) -> None:
    import sys

    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


_extend_path(REPO_ROOT / "projects" / "slo-copilot" / "src")
_extend_path(REPO_ROOT / "projects" / "t-rag" / "src")
_extend_path(REPO_ROOT / "projects" / "topology-graph-rca" / "src")
_extend_path(REPO_ROOT / "projects" / "caat")


class SamplingPolicy(BaseModel):
    sampling_action: Optional[str] = None
    sampling_rate: Optional[float] = None


class TraceQuery(BaseModel):
    trace_path: str


class TopologyQuery(BaseModel):
    manifest_paths: Optional[list[str]] = None
    trace_paths: Optional[list[str]] = None


class OpenSLOPayload(BaseModel):
    payload: Dict[str, Any] | list


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/policy/sampling")
def get_sampling_policy(actor: ActorContext = Depends(require_auth)) -> Dict[str, Any]:
    authorize(actor, "policy.read")
    state = load_state(CONTROL_STORE)
    audit_event("policy.read", actor, details={"has_policy": bool(state.get("sampling_policy"))})
    return state.get("sampling_policy", {})


@app.post("/policy/sampling")
def set_sampling_policy(policy: SamplingPolicy, actor: ActorContext = Depends(require_auth)) -> Dict[str, Any]:
    authorize(actor, "policy.write")
    state = load_state(CONTROL_STORE)
    payload = policy.dict(exclude_none=True)
    if not payload:
        audit_event("policy.write", actor, status="invalid", details={"reason": "empty_payload"})
        raise HTTPException(status_code=400, detail="Provide sampling_action or sampling_rate")
    state["sampling_policy"] = payload
    save_state(CONTROL_STORE, state)
    audit_event("policy.write", actor, details={"payload_keys": list(payload.keys())})
    return payload


@app.get("/slo/export")
def export_slos(actor: ActorContext = Depends(require_auth)) -> Dict[str, Any]:
    authorize(actor, "slo.read")
    if not SLO_STORE.exists():
        audit_event("slo.read", actor, status="not_found", details={"path": str(SLO_STORE)})
        raise HTTPException(status_code=404, detail=f"SLO store not found: {SLO_STORE}")
    audit_event("slo.read", actor, details={"path": str(SLO_STORE)})
    return json.loads(SLO_STORE.read_text(encoding="utf-8"))


@app.post("/slo/validate")
def validate_openslo(payload: OpenSLOPayload, actor: ActorContext = Depends(require_auth)) -> Dict[str, Any]:
    authorize(actor, "slo.validate")
    try:
        from slo_copilot.openslo_validator import validate_openslo_payload
    except Exception as exc:
        audit_event("slo.validate", actor, status="unavailable", details={"error": str(exc)})
        raise HTTPException(status_code=503, detail=f"OpenSLO validator unavailable: {exc}") from exc
    ok, errors = validate_openslo_payload(payload.payload)
    audit_event("slo.validate", actor, details={"valid": ok, "error_count": len(errors)})
    return {"valid": ok, "errors": errors}


@app.post("/rca/query")
def rca_query(query: TraceQuery, actor: ActorContext = Depends(require_auth)) -> Dict[str, Any]:
    authorize(actor, "rca.query")
    try:
        from t_rag import service as trag_service
    except Exception as exc:
        audit_event("rca.query", actor, status="unavailable", details={"error": str(exc)})
        raise HTTPException(status_code=503, detail=f"T-RAG unavailable: {exc}") from exc
    if not Path(query.trace_path).exists():
        audit_event("rca.query", actor, status="not_found", details={"trace_path": query.trace_path})
        raise HTTPException(status_code=404, detail="Trace path not found")
    result = trag_service.run(query.trace_path)
    audit_event("rca.query", actor, details={"trace_path": query.trace_path})
    return result


@app.post("/topology/analyze")
def topology_analyze(query: TopologyQuery, actor: ActorContext = Depends(require_auth)) -> Dict[str, Any]:
    authorize(actor, "topology.analyze")
    try:
        from topology_graph_rca.analyzer import TopologyAnalyzer
    except Exception as exc:
        audit_event("topology.analyze", actor, status="unavailable", details={"error": str(exc)})
        raise HTTPException(status_code=503, detail=f"Topology RCA unavailable: {exc}") from exc
    analyzer = TopologyAnalyzer()
    report = analyzer.analyze(manifest_paths=query.manifest_paths, trace_paths=query.trace_paths)
    audit_event(
        "topology.analyze",
        actor,
        details={
            "manifest_count": len(query.manifest_paths or []),
            "trace_count": len(query.trace_paths or []),
        },
    )
    return report.__dict__


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8088)
