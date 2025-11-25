# Cost‑Aware Adaptive Telemetry (CAAT)

CAAT is the first project in the MindOps initiative.  It brings together
kernel‑level instrumentation, reinforcement learning and generative AI to
deliver an observability system that automatically adapts telemetry volume
based on runtime conditions and budget constraints.  Instead of blindly
collecting all logs, traces and metrics, CAAT continuously tunes what is
recorded, ensuring that you capture the right signals at the right time
without breaking the bank.

![CAAT Architecture](../docs/images/caat_architecture.png)

## Components

CAAT consists of several distinct components working together:

* **eBPF Runtime Sensing Layer** – low‑overhead kernel probes that collect
  detailed system telemetry (system calls, network events, etc.)
  using eBPF.  The probes are orchestrated from Go and run as a
  DaemonSet on each node.

* **Trace‑Native RAG Contextual Layer** – a Python service that
  retrieves telemetry events (logs, metrics and traces) and uses
  Retrieval‑Augmented Generation (RAG) via OpenAI’s APIs to provide
  context and natural‑language explanations for anomalies.

* **RL‑based Telemetry Optimizer** – a reinforcement learning policy
  engine, written in Python, that observes runtime context and
  continuously adjusts telemetry sampling levels and log verbosity to
  maximize signal‑to‑noise while staying within a budget envelope.

* **Telemetry Budget Engine** – a forecasting module that predicts how
  much telemetry data will be generated and how that translates into
  cost over time using ARIMA and LSTM models.  It feeds its forecasts
  back into the RL optimizer so that it can stay within a specified
  budget.

* **Multi‑Cloud Control Plane** – integration code that applies policy
  decisions across Kubernetes clusters and cloud providers (AWS, Azure,
  GCP) via OpenTelemetry collectors and cloud observability APIs.

CAAT also ships with sample Kubernetes deployments, Grafana dashboards and
detailed documentation to help you get started.

## Getting Started

1. Review the project architecture and code in this directory.
2. Build and load the eBPF probes (see `ebpf_probes/`).
3. Deploy the RL policy engine, budget engine and RAG layer (see
   `rl_policy_engine/`, `telemetry_budget_engine/`, `rag_context_layer/`).
4. Install the Helm chart under `deploy/helm/caat` on your Kubernetes
   cluster.
5. Explore the dashboards in the `grafana/` directory.

For detailed instructions, see the documentation in the `docs/` folder.