# ebpf_bot Package

Core modules for the coverage bot.

## Modules

- `coverage_bot.py`: Maintains coverage map, emits `get_coverage` span with events/attributes.
- `orchestrator.py`: Chooses next probe, emits `decide_next_probe` span with decision attributes/events.
- `pipeline.py`: Orchestrates the workflow, emits `unified_pipeline_decision` span, metrics, and correlated logs.
- `processor.py`: Simulates signal processing under `process_signal` span.
- `store.py`: Simulates persistence under `store_save_signal` and `store_load_signal` spans.
- `injector.py`: Simulates probe injection under `inject_probe` span.
- `receiver.py`: Simulates receiving signals under `receive_signal` span.
- `cli.py`: CLI entrypoint (if used).

## Interactions

- `UnifiedPipeline` calls `CoverageBot.get_coverage()`, `CoverageOrchestrator.decide_next_probe()`, then `SignalProcessor.process()` and `SignalStore.save/load()`.
- Each module emits a tracing span so the end-to-end trace shows the full decision flow.
