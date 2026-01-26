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

## Output

The CLI prints a JSON report with:

- `zero_touch`: collector plan and patch hints
- `slo_copilot`: SLO evaluations, tests, and guardrails
- `caat`: sampling recommendation
- `t_rag`: RCA output (when triggered)
- `warnings`: missing integrations or dependency issues
