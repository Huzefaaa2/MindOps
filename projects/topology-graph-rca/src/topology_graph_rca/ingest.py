"""Topology ingestion from manifests and traces."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .models import Edge, Node

try:  # optional dependency
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


def load_manifests(paths: Iterable[str]) -> List[Dict[str, object]]:
    docs: List[Dict[str, object]] = []
    for path_str in paths:
        path = Path(path_str)
        if path.is_dir():
            for file_path in sorted(path.glob("**/*")):
                if file_path.suffix.lower() in {".yaml", ".yml", ".json"}:
                    docs.extend(_load_file(file_path))
        else:
            docs.extend(_load_file(path))
    return [doc for doc in docs if doc]


def _load_file(path: Path) -> List[Dict[str, object]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return _unwrap_list(json.loads(path.read_text(encoding="utf-8")))
    if suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("PyYAML is required to parse YAML manifests. Install pyyaml.")
        docs = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
        results: List[Dict[str, object]] = []
        for doc in docs:
            results.extend(_unwrap_list(doc))
        return results
    raise ValueError(f"Unsupported manifest type: {path}")


def _unwrap_list(data: object) -> List[Dict[str, object]]:
    if data is None:
        return []
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict) and data.get("kind") == "List":
        items = data.get("items", [])
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    if isinstance(data, dict):
        return [data]
    return []


def nodes_from_manifests(documents: Iterable[Dict[str, object]]) -> List[Node]:
    nodes: List[Node] = []
    for doc in documents:
        kind = str(doc.get("kind", ""))
        if kind not in {"Deployment", "StatefulSet", "DaemonSet", "Service"}:
            continue
        metadata = doc.get("metadata", {}) or {}
        name = str(metadata.get("name", "unknown"))
        namespace = str(metadata.get("namespace", "default"))
        labels = metadata.get("labels", {}) or {}
        node_id = f"{namespace}/{name}"
        nodes.append(Node(node_id=node_id, name=name, namespace=namespace, kind=kind, labels=labels))
    return nodes


def edges_from_traces(trace_paths: Iterable[str]) -> Tuple[List[Edge], Dict[str, Dict[str, float]]]:
    edges: Dict[Tuple[str, str], int] = {}
    stats: Dict[str, Dict[str, float]] = {}
    spans = []
    for path in trace_paths:
        spans.extend(_load_spans(Path(path)))
    for span in spans:
        service = span.get("service_name") or "unknown"
        parent_service = span.get("parent_service")
        _update_stats(stats, service, span)
        if parent_service and parent_service != service:
            key = (parent_service, service)
            edges[key] = edges.get(key, 0) + 1
    edge_list = [Edge(source=src, target=dst, weight=float(weight)) for (src, dst), weight in edges.items()]
    return edge_list, stats


def _load_spans(path: Path) -> List[Dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    spans: List[Dict[str, object]] = []
    if isinstance(data, list):
        for span in data:
            spans.append(_normalize_span(span, span.get("service.name") or span.get("service_name") or "unknown"))
    elif isinstance(data, dict):
        for resource in data.get("resourceSpans", []):
            service_name = _resource_service_name(resource)
            for scope in resource.get("scopeSpans", []):
                for span in scope.get("spans", []):
                    spans.append(_normalize_span(span, service_name))
    _attach_parent_services(spans)
    return spans


def _attach_parent_services(spans: List[Dict[str, object]]) -> None:
    index = {span.get("span_id"): span for span in spans}
    for span in spans:
        parent_id = span.get("parent_id")
        parent = index.get(parent_id)
        if parent:
            span["parent_service"] = parent.get("service_name")


def _resource_service_name(resource: Dict[str, object]) -> str:
    attributes = resource.get("resource", {}).get("attributes", []) if "resource" in resource else resource.get("attributes", [])
    for attr in attributes or []:
        key = attr.get("key") or attr.get("name")
        if key == "service.name":
            value = attr.get("value")
            if isinstance(value, dict):
                return value.get("stringValue") or value.get("value") or "unknown"
            return value or "unknown"
    return "unknown"


def _normalize_span(span: Dict[str, object], service_name: str) -> Dict[str, object]:
    attributes = {}
    for attribute in span.get("attributes", []) or []:
        key = attribute.get("key") or attribute.get("name")
        value = attribute.get("value")
        if isinstance(value, dict):
            value = next(iter(value.values()))
        attributes[key] = value
    parent_id = span.get("parentSpanId") or span.get("parentSpanID")
    return {
        "span_id": span.get("spanId") or span.get("span_id"),
        "parent_id": parent_id,
        "service_name": service_name,
        "status": span.get("status", {}),
        "attributes": attributes,
    }


def _update_stats(stats: Dict[str, Dict[str, float]], service: str, span: Dict[str, object]) -> None:
    entry = stats.setdefault(service, {"total": 0.0, "errors": 0.0})
    entry["total"] += 1.0
    if _is_error(span):
        entry["errors"] += 1.0


def _is_error(span: Dict[str, object]) -> bool:
    status = span.get("status") or {}
    code = str(status.get("code", "")).upper()
    if code in {"ERROR", "STATUS_CODE_ERROR"}:
        return True
    attrs = span.get("attributes", {}) or {}
    status_code = attrs.get("http.status_code") or attrs.get("http.status")
    if isinstance(status_code, str) and status_code.isdigit():
        status_code = int(status_code)
    if isinstance(status_code, (int, float)) and status_code >= 500:
        return True
    if "exception.message" in attrs or "exception.type" in attrs:
        return True
    return False
