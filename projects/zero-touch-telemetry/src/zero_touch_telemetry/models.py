"""Data models for Zero-Touch Telemetry."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ContainerSpec:
    name: str
    image: str
    ports: List[int] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)


@dataclass
class WorkloadSpec:
    name: str
    namespace: str
    kind: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    containers: List[ContainerSpec]


@dataclass
class ServiceSpec:
    name: str
    namespace: str
    selector: Dict[str, str]
    ports: List[int]


@dataclass
class DiscoveredService:
    name: str
    namespace: str
    workload: Optional[WorkloadSpec]
    service: Optional[ServiceSpec]
    language: str
    ports: List[int]
    labels: Dict[str, str]


@dataclass
class InstrumentationPlan:
    service_name: str
    namespace: str
    language: str
    otlp_endpoint: str
    env: Dict[str, str]


@dataclass
class PatchInstruction:
    workload_name: str
    namespace: str
    kind: str
    description: str
    patch: Dict[str, object]


@dataclass
class CollectorPlan:
    mode: str
    namespace: str
    sampling_rate: float
    exporters: List[str]
    config_yaml: str
    manifest_yaml: str
    instrumentation: List[InstrumentationPlan]
    patches: List[PatchInstruction]
    discovered: List[DiscoveredService]


@dataclass
class ZeroTouchPlan:
    collector: CollectorPlan
    warnings: List[str] = field(default_factory=list)
