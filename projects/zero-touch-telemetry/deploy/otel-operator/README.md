# OpenTelemetry Operator Auto-Instrumentation

This folder contains sample OpenTelemetry Operator `Instrumentation` resources and
workload annotations to enable auto-instrumentation.

## Apply Instrumentation resources

```bash
kubectl apply -f instrumentation.yaml
```

This creates Instrumentation CRs for:

- Java
- Node.js
- Python
- .NET

## Annotate workloads

Use the annotation matching the language. Example:

```yaml
metadata:
  annotations:
    instrumentation.opentelemetry.io/inject-python: "observability/python"
```

You can patch an existing Deployment with:

```bash
kubectl patch deployment checkout -n storefront \
  --type merge \
  -p '{"spec":{"template":{"metadata":{"annotations":{"instrumentation.opentelemetry.io/inject-python":"observability/python"}}}}}'
```

## Notes

- Update the `exporter.endpoint` in `instrumentation.yaml` to point at your collector.
- Set the namespace to match where you deploy the Instrumentation CRs.
