"""Collector config and manifest generation."""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple


def build_collector_config(
    sampling_rate: float,
    exporters: List[str],
    otlp_export_endpoint: Optional[str] = None,
) -> str:
    processor_blocks = ["memory_limiter", "batch"]
    if sampling_rate < 1.0:
        processor_blocks.insert(0, "probabilistic_sampler")
    exporters_config = _exporter_config(exporters, otlp_export_endpoint)
    exporters_list = ", ".join(exporters)
    return f"""receivers:
  otlp:
    protocols:
      grpc:
      http:

processors:
  memory_limiter:
    check_interval: 1s
    limit_mib: 400
  batch:
    timeout: 1s
    send_batch_size: 1024
""" + (
        f"  probabilistic_sampler:\n    sampling_percentage: {sampling_rate * 100:.1f}\n"
        if sampling_rate < 1.0
        else ""
    ) + f"""
exporters:
{exporters_config}

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [{', '.join(processor_blocks)}]
      exporters: [{exporters_list}]
    metrics:
      receivers: [otlp]
      processors: [{', '.join(processor_blocks)}]
      exporters: [{exporters_list}]
    logs:
      receivers: [otlp]
      processors: [{', '.join(processor_blocks)}]
      exporters: [{exporters_list}]
"""


def _exporter_config(exporters: List[str], otlp_export_endpoint: Optional[str]) -> str:
    blocks: List[str] = []
    for exporter in exporters:
        if exporter == "logging":
            blocks.append("  logging:\n    loglevel: info")
        elif exporter == "otlp":
            endpoint = otlp_export_endpoint or "http://otel-collector-gateway:4317"
            blocks.append(
                "  otlp:\n"
                f"    endpoint: {endpoint}\n"
                "    tls:\n"
                "      insecure: true"
            )
    return "\n".join(blocks)


def build_gateway_manifest(namespace: str, config_yaml: str) -> str:
    return _collector_manifest(
        kind="Deployment",
        name="otel-collector-gateway",
        namespace=namespace,
        config_yaml=config_yaml,
        labels={"app": "otel-collector-gateway"},
    )


def build_daemonset_manifest(namespace: str, config_yaml: str) -> str:
    return _collector_manifest(
        kind="DaemonSet",
        name="otel-collector-daemonset",
        namespace=namespace,
        config_yaml=config_yaml,
        labels={"app": "otel-collector-daemonset"},
    )


def _collector_manifest(
    kind: str,
    name: str,
    namespace: str,
    config_yaml: str,
    labels: Dict[str, str],
) -> str:
    label_block = "\n".join([f"    {k}: {v}" for k, v in labels.items()])
    return f"""---
apiVersion: v1
kind: ConfigMap
metadata:
  name: {name}-config
  namespace: {namespace}
data:
  otel-collector-config.yaml: |
{_indent(config_yaml, 4)}
---
apiVersion: v1
kind: Service
metadata:
  name: {name}
  namespace: {namespace}
spec:
  selector:
{label_block}
  ports:
    - name: otlp-grpc
      port: 4317
      targetPort: 4317
    - name: otlp-http
      port: 4318
      targetPort: 4318
---
apiVersion: apps/v1
kind: {kind}
metadata:
  name: {name}
  namespace: {namespace}
spec:
  selector:
    matchLabels:
{label_block}
  template:
    metadata:
      labels:
{label_block}
    spec:
      containers:
        - name: otel-collector
          image: otel/opentelemetry-collector:0.97.0
          args: ["--config=/etc/otel/otel-collector-config.yaml"]
          ports:
            - containerPort: 4317
            - containerPort: 4318
          volumeMounts:
            - name: otel-config
              mountPath: /etc/otel
      volumes:
        - name: otel-config
          configMap:
            name: {name}-config
"""


def _indent(text: str, spaces: int) -> str:
    pad = " " * spaces
    return "\n".join(pad + line if line.strip() else pad for line in text.splitlines())


def build_sidecar_patch(otlp_endpoint: str, service_name: str) -> Tuple[str, Dict[str, object]]:
    description = "Inject OTLP exporter env vars to send telemetry to sidecar collector."
    patch = {
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": "${CONTAINER_NAME}",
                            "env": [
                                {"name": "OTEL_EXPORTER_OTLP_ENDPOINT", "value": otlp_endpoint},
                                {"name": "OTEL_SERVICE_NAME", "value": service_name},
                            ],
                        }
                    ]
                }
            }
        }
    }
    return description, patch
