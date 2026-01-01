# Source

Python package source for the eBPF bot.

## Layout

- `ebpf_bot/`: main package with pipeline and module implementations.

The package is organized so `UnifiedPipeline` orchestrates coverage collection, probe selection, processing, and storage while emitting telemetry.
