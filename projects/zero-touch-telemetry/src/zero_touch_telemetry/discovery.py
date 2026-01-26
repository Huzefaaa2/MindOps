"""Discovery utilities for Kubernetes manifests."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .language import detect_language
from .models import ContainerSpec, DiscoveredService, ServiceSpec, WorkloadSpec

try:  # optional dependency
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


SUPPORTED_WORKLOADS = {"Deployment", "StatefulSet", "DaemonSet"}


def load_manifests(paths: Iterable[str]) -> List[Dict[str, object]]:
    documents: List[Dict[str, object]] = []
    for path_str in paths:
        path = Path(path_str)
        if path.is_dir():
            for file_path in sorted(path.glob("**/*")):
                if file_path.suffix.lower() in {".yaml", ".yml", ".json"}:
                    documents.extend(_load_file(file_path))
        else:
            documents.extend(_load_file(path))
    return [doc for doc in documents if doc]


def _load_file(path: Path) -> List[Dict[str, object]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return _load_json(path)
    if suffix in {".yaml", ".yml"}:
        return _load_yaml(path)
    raise ValueError(f"Unsupported manifest type: {path}")


def _load_json(path: Path) -> List[Dict[str, object]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return _unwrap_list(data)


def _load_yaml(path: Path) -> List[Dict[str, object]]:
    if yaml is None:
        raise RuntimeError("PyYAML is required to parse YAML manifests. Install pyyaml.")
    with path.open("r", encoding="utf-8") as handle:
        docs = list(yaml.safe_load_all(handle))
    results: List[Dict[str, object]] = []
    for doc in docs:
        results.extend(_unwrap_list(doc))
    return results


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


def discover_services(paths: Iterable[str]) -> List[DiscoveredService]:
    documents = load_manifests(paths)
    workloads = _extract_workloads(documents)
    services = _extract_services(documents)

    discovered: List[DiscoveredService] = []
    matched_workloads = set()

    for service in services:
        matched = _match_workloads(service, workloads)
        for workload in matched:
            matched_workloads.add(workload.name)
            discovered.append(_make_discovered(service, workload))
        if not matched:
            discovered.append(_make_discovered(service, None))

    for workload in workloads:
        if workload.name in matched_workloads:
            continue
        discovered.append(_make_discovered(None, workload))

    return discovered


def _extract_workloads(documents: Iterable[Dict[str, object]]) -> List[WorkloadSpec]:
    workloads: List[WorkloadSpec] = []
    for doc in documents:
        kind = str(doc.get("kind", ""))
        if kind not in SUPPORTED_WORKLOADS:
            continue
        metadata = doc.get("metadata", {}) or {}
        spec = doc.get("spec", {}) or {}
        template = spec.get("template", {}) or {}
        pod_spec = template.get("spec", {}) or {}
        containers = pod_spec.get("containers", []) or []
        workloads.append(
            WorkloadSpec(
                name=str(metadata.get("name", "unknown")),
                namespace=str(metadata.get("namespace", "default")),
                kind=kind,
                labels=metadata.get("labels", {}) or {},
                annotations=metadata.get("annotations", {}) or {},
                containers=_extract_containers(containers),
            )
        )
    return workloads


def _extract_containers(raw: Iterable[object]) -> List[ContainerSpec]:
    containers: List[ContainerSpec] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        ports = []
        for port in item.get("ports", []) or []:
            if isinstance(port, dict) and "containerPort" in port:
                ports.append(int(port["containerPort"]))
        env = {}
        for env_item in item.get("env", []) or []:
            if isinstance(env_item, dict) and "name" in env_item:
                value = env_item.get("value")
                if value is not None:
                    env[str(env_item["name"])] = str(value)
        containers.append(
            ContainerSpec(
                name=str(item.get("name", "unknown")),
                image=str(item.get("image", "")),
                ports=ports,
                env=env,
            )
        )
    return containers


def _extract_services(documents: Iterable[Dict[str, object]]) -> List[ServiceSpec]:
    services: List[ServiceSpec] = []
    for doc in documents:
        if str(doc.get("kind", "")) != "Service":
            continue
        metadata = doc.get("metadata", {}) or {}
        spec = doc.get("spec", {}) or {}
        ports = []
        for port in spec.get("ports", []) or []:
            if isinstance(port, dict) and "port" in port:
                ports.append(int(port["port"]))
        services.append(
            ServiceSpec(
                name=str(metadata.get("name", "unknown")),
                namespace=str(metadata.get("namespace", "default")),
                selector=spec.get("selector", {}) or {},
                ports=ports,
            )
        )
    return services


def _match_workloads(service: ServiceSpec, workloads: List[WorkloadSpec]) -> List[WorkloadSpec]:
    if not service.selector:
        return []
    matched = []
    for workload in workloads:
        if workload.namespace != service.namespace:
            continue
        if _selector_match(service.selector, workload.labels):
            matched.append(workload)
    return matched


def _selector_match(selector: Dict[str, str], labels: Dict[str, str]) -> bool:
    for key, value in selector.items():
        if labels.get(key) != value:
            return False
    return True


def _make_discovered(service: Optional[ServiceSpec], workload: Optional[WorkloadSpec]) -> DiscoveredService:
    name = service.name if service else workload.name if workload else "unknown"
    namespace = service.namespace if service else workload.namespace if workload else "default"
    labels = workload.labels if workload else {}
    language = "unknown"
    ports: List[int] = []
    if workload and workload.containers:
        language = detect_language(workload.containers[0].image, labels)
        for container in workload.containers:
            ports.extend(container.ports)
    if service:
        ports.extend(service.ports)
    ports = sorted({p for p in ports if p})
    return DiscoveredService(
        name=name,
        namespace=namespace,
        workload=workload,
        service=service,
        language=language,
        ports=ports,
        labels=labels,
    )
