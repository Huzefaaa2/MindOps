# MindOps Orchestrator CLI

A unified CLI to run CAAT + SLO Copilot + Zero‑Touch Telemetry + T‑RAG flows in one command.

## Usage

```bash
PYTHONPATH=projects/mindops-orchestrator/src python3 -m mindops_orchestrator.cli \
  --trace projects/slo-copilot/examples/sample_trace.json \
  --manifests projects/zero-touch-telemetry/examples/sample_k8s.yaml \
  --telemetry-volume 0.9 \
  --telemetry-volume 1.1
```

Apply Zero‑Touch plan (diff only):

```bash
PYTHONPATH=projects/mindops-orchestrator/src python3 -m mindops_orchestrator.cli \
  --manifests projects/zero-touch-telemetry/examples/sample_k8s.yaml \
  --zero-touch-diff-only
```

Export structured artifacts:

```bash
PYTHONPATH=projects/mindops-orchestrator/src python3 -m mindops_orchestrator.cli \
  --trace projects/slo-copilot/examples/sample_trace.json \
  --manifests projects/zero-touch-telemetry/examples/sample_k8s.yaml \
  --export-dir out
```

## Output

The CLI prints a JSON report with:

- `zero_touch`: collector plan and patch hints
- `slo_copilot`: SLO evaluations, tests, and guardrails
- `caat`: sampling recommendation
- `t_rag`: RCA output (when triggered)
- `warnings`: missing integrations or dependency issues

Structured export layout:

| Path | Contents |
| --- | --- |
| `out/orchestrator_report.json` | Full consolidated report |
| `out/zero_touch/plan.json` | Zero‑Touch plan |
| `out/zero_touch/collector-config.yaml` | Collector config (if present) |
| `out/zero_touch/collector-manifest.yaml` | Collector manifest (if present) |
| `out/slo_copilot/report.json` | SLO Copilot report |
