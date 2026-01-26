"""Planning logic for Zero-Touch Telemetry."""
from __future__ import annotations

from typing import Dict, List, Optional

from .manifests import (
    build_collector_config,
    build_daemonset_manifest,
    build_gateway_manifest,
    build_sidecar_patch,
)
from .models import CollectorPlan, DiscoveredService, InstrumentationPlan, PatchInstruction, ZeroTouchPlan


class ZeroTouchPlanner:
    def __init__(
        self,
        mode: str = "auto",
        namespace: str = "observability",
        exporters: Optional[List[str]] = None,
        otlp_export_endpoint: Optional[str] = None,
        sampling_rate: float = 1.0,
    ) -> None:
        self.mode = mode
        self.namespace = namespace
        self.exporters = exporters or ["logging"]
        self.otlp_export_endpoint = otlp_export_endpoint
        self.sampling_rate = sampling_rate

    def plan(self, discovered: List[DiscoveredService]) -> ZeroTouchPlan:
        mode = self._resolve_mode(discovered)
        warnings: List[str] = []
        if mode == "auto":
            warnings.append("Fell back to gateway mode due to missing workload signals.")
            mode = "gateway"

        config_yaml = build_collector_config(
            sampling_rate=self.sampling_rate,
            exporters=self.exporters,
            otlp_export_endpoint=self.otlp_export_endpoint,
        )

        manifest_yaml = ""
        otlp_endpoint = ""
        if mode == "gateway":
            manifest_yaml = build_gateway_manifest(self.namespace, config_yaml)
            otlp_endpoint = f"http://otel-collector-gateway.{self.namespace}:4317"
        elif mode == "daemonset":
            manifest_yaml = build_daemonset_manifest(self.namespace, config_yaml)
            otlp_endpoint = f"http://otel-collector-daemonset.{self.namespace}:4317"
        elif mode == "sidecar":
            otlp_endpoint = "http://localhost:4317"
            manifest_yaml = _sidecar_manifest_stub(self.namespace, config_yaml)
        else:
            warnings.append(f"Unknown mode {mode}, defaulting to gateway.")
            manifest_yaml = build_gateway_manifest(self.namespace, config_yaml)
            otlp_endpoint = f"http://otel-collector-gateway.{self.namespace}:4317"
            mode = "gateway"

        instrumentation = _build_instrumentation(discovered, otlp_endpoint)
        patches = _build_patches(discovered, otlp_endpoint, mode)

        collector_plan = CollectorPlan(
            mode=mode,
            namespace=self.namespace,
            sampling_rate=self.sampling_rate,
            exporters=self.exporters,
            config_yaml=config_yaml,
            manifest_yaml=manifest_yaml,
            instrumentation=instrumentation,
            patches=patches,
            discovered=discovered,
        )
        return ZeroTouchPlan(collector=collector_plan, warnings=warnings)

    def _resolve_mode(self, discovered: List[DiscoveredService]) -> str:
        if self.mode != "auto":
            return self.mode
        workloads = [item.workload for item in discovered if item.workload]
        if any(wl.kind == "DaemonSet" for wl in workloads):
            return "daemonset"
        if len(workloads) <= 5 and workloads:
            return "sidecar"
        if workloads:
            return "gateway"
        return "auto"


def _build_instrumentation(
    discovered: List[DiscoveredService],
    otlp_endpoint: str,
) -> List[InstrumentationPlan]:
    plans: List[InstrumentationPlan] = []
    for item in discovered:
        env = {
            "OTEL_EXPORTER_OTLP_ENDPOINT": otlp_endpoint,
            "OTEL_SERVICE_NAME": item.name,
            "OTEL_RESOURCE_ATTRIBUTES": f"service.namespace={item.namespace},service.name={item.name}",
        }
        plans.append(
            InstrumentationPlan(
                service_name=item.name,
                namespace=item.namespace,
                language=item.language,
                otlp_endpoint=otlp_endpoint,
                env=env,
            )
        )
    return plans


def _build_patches(
    discovered: List[DiscoveredService],
    otlp_endpoint: str,
    mode: str,
) -> List[PatchInstruction]:
    patches: List[PatchInstruction] = []
    for item in discovered:
        if not item.workload:
            continue
        description, patch = build_sidecar_patch(otlp_endpoint, item.name)
        patches.append(
            PatchInstruction(
                workload_name=item.workload.name,
                namespace=item.workload.namespace,
                kind=item.workload.kind,
                description=description,
                patch=_expand_patch_containers(patch, item.workload),
            )
        )
    if mode != "sidecar":
        for patch in patches:
            patch.description = "Inject OTLP exporter env vars to send telemetry to collector gateway."
    return patches


def _expand_patch_containers(patch: Dict[str, object], workload) -> Dict[str, object]:
    containers = []
    for container in workload.containers:
        container_patch = {
            "name": container.name,
            "env": patch["spec"]["template"]["spec"]["containers"][0]["env"],
        }
        containers.append(container_patch)
    return {
        "spec": {
            "template": {
                "spec": {
                    "containers": containers,
                }
            }
        }
    }


def _sidecar_manifest_stub(namespace: str, config_yaml: str) -> str:
    return (
        "---\n"
        "apiVersion: v1\n"
        "kind: ConfigMap\n"
        f"metadata:\n  name: otel-collector-sidecar-config\n  namespace: {namespace}\n"
        "data:\n  otel-collector-config.yaml: |\n"
        + _indent(config_yaml, 4)
        + "\n# Sidecar injection required: mount the config and run otel/opentelemetry-collector in each workload.\n"
    )


def _indent(text: str, spaces: int) -> str:
    pad = " " * spaces
    return "\n".join(pad + line if line.strip() else pad for line in text.splitlines())
