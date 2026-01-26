# Synthetic Incident: Checkout Latency Spike

## Summary
A latency spike is detected in the checkout path after a minor deploy. The incident
is designed to exercise MindOps end-to-end: Zero-Touch planning, SLO Copilot
validation, and RCA via T-RAG + Topology Graph RCA.

## Impact
- Scope: checkout-service, payment-service, inventory-service
- Symptoms: p95 latency > 1.8s, error rate rising to 3%
- User impact: elevated cart abandonment

## Timeline (UTC)
- T-00:05: Deploy checkout-service v1.12.3
- T+00:05: SLO burn rate alert fires
- T+00:10: T-RAG suggests downstream dependency regression
- T+00:15: Topology RCA flags payment-service latency edge
- T+00:20: Mitigation: rollback payment-service to v2.4.1

## Expected Observations
- Elevated latency on `checkout-service` spans
- Increased error events on `payment-service` spans
- Topology graph highlights a high-latency edge from checkout -> payment

## Demo Inputs
- SLOs: `assets/slo_export.json`
- OpenSLO bundle: `assets/openslo_bundle.json`
- Manifests: `manifests/sample_k8s.yaml`
- Trace sample: `projects/slo-copilot/examples/sample_trace.json`

## Demo Outputs
- RCA output: `assets/rca_output.json`
- Topology report: `out/topology_report.json`
- Orchestrator bundle: `out/` (if using `--export-dir`)
