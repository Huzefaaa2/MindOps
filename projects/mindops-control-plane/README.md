# MindOps Control Plane API

A lightweight gateway that exposes key MindOps capabilities via HTTP:

- Policy updates (sampling knobs)
- SLO export + validation
- RCA queries (T‑RAG)
- Topology RCA analysis

This service is intentionally minimal and acts as a façade over the existing project
modules in this repository.

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

PYTHONPATH=src python3 -m mindops_control_plane.app
```

The server listens on `http://localhost:8088`.

## Endpoints

| Endpoint | Method | Description |
| --- | --- | --- |
| `/health` | GET | Health check |
| `/policy/sampling` | GET/POST | Get/update sampling policy |
| `/slo/export` | GET | Return persisted SLOs from store |
| `/slo/validate` | POST | Validate OpenSLO payload |
| `/rca/query` | POST | Run T‑RAG RCA (trace path) |
| `/topology/analyze` | POST | Run Topology RCA (manifest + trace paths) |

## Examples

```bash
curl -s http://localhost:8088/health
```

```bash
curl -s -X POST http://localhost:8088/policy/sampling \
  -H 'Content-Type: application/json' \
  -d '{"sampling_action":"decrease_sampling"}'
```

```bash
curl -s -X POST http://localhost:8088/rca/query \
  -H 'Content-Type: application/json' \
  -d '{"trace_path":"projects/slo-copilot/examples/sample_trace.json"}'
```

```bash
curl -s http://localhost:8088/slo/export \
  -H 'X-API-Key: your-key' \
  -H 'X-Actor: sre-user'
```

## Configuration

- `CONTROL_PLANE_STORE`: Path to JSON store for policies (default: `data/control_plane_state.json`)
- `SLO_STORE_PATH`: Path to SLO store (default: `projects/slo-copilot/data/slo_store.json`)
- `CONTROL_PLANE_API_KEY`: If set, require `X-API-Key` or `Authorization: Bearer` for all endpoints.
- `CONTROL_PLANE_AUTHZ_MODE`: `allow-all` (default), `scoped`, or `deny-all` authz stub.
- `CONTROL_PLANE_AUDIT_LOG`: Audit log path (default: `data/audit.log`)

## Notes

- This API is designed for local or lab use; production deployments should add TLS,
  RBAC-backed authz, and durable audit logging.
