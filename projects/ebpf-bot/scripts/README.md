# Scripts

Helper scripts for emitting telemetry during local runs.

## Files

- `emit_trace.py`: Runs `UnifiedPipeline().collect_and_decide()` and emits spans, metrics, and logs via the pipeline setup. Adds a short sleep for flush.
- `emit_telemetry.py`: Explicitly configures OTLP exporters for traces, metrics, and logs, then runs the pipeline and emits a sample metric and log.

## Usage

From `projects/ebpf-bot`:

```bash
python3 scripts/emit_trace.py
python3 scripts/emit_telemetry.py
```
