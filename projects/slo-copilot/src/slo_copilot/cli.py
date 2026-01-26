"""Command-line interface for SLO Copilot."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Optional

from .copilot import SLOCopilot
from .exports import export_open_slo, export_slo_json
from .openslo_validator import validate_openslo_payload, validate_openslo_file
from .openslo_yaml import export_open_slo_yaml
from .slo_store import SLOStore


def _split_floats(values: Optional[List[str]]) -> Optional[List[float]]:
    if not values:
        return None
    return [float(value) for value in values]


def main() -> None:
    parser = argparse.ArgumentParser(description="SLO Copilot + Trace-Based Testing")
    parser.add_argument("--trace", required=True, help="Path to a trace JSON file")
    parser.add_argument("--telemetry-volume", action="append", help="Telemetry volume sample (repeatable)")
    parser.add_argument("--expected-signal", action="append", help="Expected eBPF signal name")
    parser.add_argument("--observed-signal", action="append", help="Observed signal name")
    parser.add_argument("--disable-caat", action="store_true", help="Disable CAAT integration")
    parser.add_argument("--disable-trag", action="store_true", help="Disable T-RAG integration")
    parser.add_argument("--disable-ebpf", action="store_true", help="Disable eBPF-bot integration")
    parser.add_argument("--export-json", help="Write SLO export JSON to path (use - for stdout)")
    parser.add_argument("--export-openslo", help="Write OpenSLO JSON to path (use - for stdout)")
    parser.add_argument("--export-openslo-yaml", help="Write OpenSLO YAML to path (use - for stdout)")
    parser.add_argument("--validate-openslo", nargs="?", const="__memory__", help="Validate OpenSLO payload or file")
    parser.add_argument("--slo-store", help="Persist SLOs to a JSON store")
    parser.add_argument("--store-mode", choices=["merge", "replace"], default="merge")
    args = parser.parse_args()

    copilot = SLOCopilot(
        enable_caat=not args.disable_caat,
        enable_trag=not args.disable_trag,
        enable_ebpf=not args.disable_ebpf,
    )

    report = copilot.run(
        trace_path=args.trace,
        telemetry_volumes=_split_floats(args.telemetry_volume),
        expected_signals=args.expected_signal,
        observed_signals=args.observed_signal,
    )

    print(json.dumps(_serialize(report), indent=2))

    if args.slo_store:
        store = SLOStore(args.slo_store)
        store.save(report.slo_candidates, mode=args.store_mode)

    if args.export_json:
        _write_json(export_slo_json(report.slo_candidates), args.export_json)
    if args.export_openslo:
        _write_json(export_open_slo(report.slo_candidates), args.export_openslo)
    if args.export_openslo_yaml:
        _write_text(export_open_slo_yaml(report.slo_candidates), args.export_openslo_yaml)
    if args.validate_openslo:
        if args.validate_openslo == "__memory__":
            payload = export_open_slo(report.slo_candidates)
            ok, errors = validate_openslo_payload(payload)
        else:
            ok, errors = validate_openslo_file(Path(args.validate_openslo))
        if not ok:
            raise SystemExit(f"OpenSLO validation failed: {errors}")


def _serialize(obj):
    if hasattr(obj, "__dict__"):
        return {key: _serialize(value) for key, value in obj.__dict__.items()}
    if isinstance(obj, list):
        return [_serialize(item) for item in obj]
    if isinstance(obj, dict):
        return {key: _serialize(value) for key, value in obj.items()}
    return obj


def _write_json(payload, target: str) -> None:
    data = json.dumps(payload, indent=2)
    if target == "-":
        print(data)
        return
    Path(target).write_text(data, encoding="utf-8")


def _write_text(payload: str, target: str) -> None:
    if target == "-":
        print(payload)
        return
    Path(target).write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()
