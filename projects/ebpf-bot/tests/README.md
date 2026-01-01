# Tests

Tests for spans, metrics, and pipeline flow.

## Highlights

- `test_end_to_end_tracing.py`: E2E trace assertions for pipeline spans and attributes.
- `test_metrics_pipeline.py`: Validates metric emission with in-memory metric reader.
- `test_tracing_integration.py`: Integration coverage for trace propagation across modules.
- `test_*_tracing.py`: Targeted span tests per module.

Tests set `ENABLE_OTLP=false` to avoid hitting a collector.
