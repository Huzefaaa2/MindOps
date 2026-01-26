"""OpenSLO validation helpers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Tuple

try:  # optional dependency
    import jsonschema  # type: ignore
except Exception:  # pragma: no cover
    jsonschema = None


ALLOWED_KINDS = {"Service", "SLI", "SLO"}


def validate_openslo_payload(payload: object, schema_path: Optional[Path] = None) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    schema_path = schema_path or _default_schema_path()
    if jsonschema and schema_path and schema_path.exists():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        try:
            jsonschema.validate(instance=payload, schema=schema)
        except jsonschema.ValidationError as exc:  # type: ignore[attr-defined]
            errors.append(str(exc.message))
        return len(errors) == 0, errors

    if not isinstance(payload, list):
        return False, ["OpenSLO payload must be a list of resources."]
    for idx, item in enumerate(payload):
        if not isinstance(item, dict):
            errors.append(f"Item {idx} must be an object.")
            continue
        kind = item.get("kind")
        if kind not in ALLOWED_KINDS:
            errors.append(f"Item {idx} has invalid kind: {kind}")
        metadata = item.get("metadata")
        if not isinstance(metadata, dict) or "name" not in metadata:
            errors.append(f"Item {idx} is missing metadata.name")
        spec = item.get("spec")
        if not isinstance(spec, dict):
            errors.append(f"Item {idx} missing spec object")
            continue
        if kind == "SLO":
            if "indicator" not in spec:
                errors.append(f"Item {idx} SLO missing indicator")
            objectives = spec.get("objectives")
            if not isinstance(objectives, list) or not objectives:
                errors.append(f"Item {idx} SLO missing objectives")
    return len(errors) == 0, errors


def validate_openslo_file(path: Path, schema_path: Optional[Path] = None) -> Tuple[bool, List[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return validate_openslo_payload(payload, schema_path=schema_path)


def _default_schema_path() -> Optional[Path]:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "schema" / "openslo_bundle.schema.json"
        if candidate.exists():
            return candidate
    return None
