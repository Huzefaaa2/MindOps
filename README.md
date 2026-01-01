# MindOps

Welcome to **MindOps**, a collection of research‐driven projects exploring the future of
observability and autonomous operations.  Each project in this repository tackles a
specific challenge in modern cloud systems and proposes an innovative solution that
combines state–of–the–art instrumentation, machine learning and AI‐assisted
analysis.  Over time this repository will host multiple projects under the
MindOps umbrella.  The first project, described below, implements an
intelligent telemetry system called **Cost‑Aware Adaptive Telemetry (CAAT)**.

## Projects

This repository follows a modular layout under the `projects/` directory.  Each
subdirectory contains a self‑contained project along with its code, deployment
scripts, documentation and examples.  A brief overview of the planned
projects is provided below.  Projects 1, 2, and 3 are implemented at the moment;
the remaining projects are placeholders for future work.

| Project | Directory | Description |
| --- | --- | --- |
| 1 | [`projects/caat`](projects/caat) | **Cost‑Aware Adaptive Telemetry (CAAT)** – an intelligent observability stack that adjusts the level of logging, tracing and metrics collection in real time based on runtime context and budget constraints. |
| 2 | [`projects/t‑rag`](projects/t-rag) | **Trace‑Native RAG for Root Cause** - T‑RAG tackles the next stage: rapid, AI‑assisted root cause analysis (RCA) using live traces, logs and metrics. |
| 3 | [`projects/ebpf‑bot`](projects/ebpf-bot) | **eBPF Coverage Bot** – Project 3 adds full observability to the ebpf-bot system by integrating OpenTelemetry-based tracing, metrics, and logging across its core modules. It captures spans for major operations like signal ingestion, processing, coverage decisions, and orchestrator logic, enhancing them with meaningful attributes and error events. Metrics such as decision counts and processing latency are emitted and exposed via Prometheus, while structured logs include trace and span correlation for streamlined debugging. The setup is fully containerized with Docker Compose, supporting Jaeger, Prometheus, and Grafana for visualization and analysis.|
| 4 | `projects/slo‑copilot` | **SLO Copilot + Trace‑Based Testing** – coming soon. |
| 5 | `projects/zero‑touch‑telemetry` | **Zero‑Touch Telemetry for Kubernetes** – coming soon. |
| 6 | `projects/pii‑guardrail` | **PII Guardrail Pre‑Ingest** – coming soon. |
| 7 | `projects/topology‑graph‑rca` | **Topology Graph RCA Engine** – coming soon. |

## Contributing

We welcome contributions!  Please read the contribution guidelines in
[`docs/contributing.md`](docs/contributing.md) for instructions on how to submit
bug fixes, feature requests or new components.  Each project directory
contains its own build and deployment instructions.

## License

This repository is licensed under the MIT License.  See
[`LICENSE`](LICENSE) for details.

## Wiki
[MindOps Wiki](https://github.com/Huzefaaa2/MindOps/wiki)
