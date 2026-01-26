"""Unified MindOps orchestrator CLI."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def main() -> None:
    parser = argparse.ArgumentParser(description="MindOps Orchestrator")
    parser.add_argument("--trace", help="Trace JSON for SLO Copilot / T-RAG")
    parser.add_argument("--manifests", action="append", help="K8s manifest path(s) for Zero-Touch")
    parser.add_argument("--telemetry-volume", action="append", help="Telemetry volume sample(s)")
    parser.add_argument("--expected-signal", action="append", help="Expected eBPF signal name")
    parser.add_argument("--observed-signal", action="append", help="Observed signal name")
    parser.add_argument("--zero-touch-mode", default="auto")
    parser.add_argument("--zero-touch-namespace", default="observability")
    parser.add_argument("--zero-touch-exporter", action="append")
    parser.add_argument("--output", help="Write orchestrator report JSON")
    args = parser.parse_args()

    repo_root = _find_repo_root()
    report: Dict[str, Any] = {
        "caat": None,
        "slo_copilot": None,
        "zero_touch": None,
        "t_rag": None,
        "warnings": [],
    }

    if repo_root is None:
        report["warnings"].append("Unable to locate repo root.")
        _emit(report, args.output)
        return

    _extend_path(repo_root / "projects" / "slo-copilot" / "src")
    _extend_path(repo_root / "projects" / "zero-touch-telemetry" / "src")
    _extend_path(repo_root / "projects" / "t-rag" / "src")
    _extend_path(repo_root / "projects" / "caat")

    if args.manifests:
        try:
            from zero_touch_telemetry.discovery import discover_services
            from zero_touch_telemetry.planner import ZeroTouchPlanner
        except Exception as exc:
            report["warnings"].append(f"Zero-Touch unavailable: {exc}")
        else:
            exporters, otlp_endpoint = _parse_exporters(args.zero_touch_exporter)
            discovered = discover_services(args.manifests)
            planner = ZeroTouchPlanner(
                mode=args.zero_touch_mode,
                namespace=args.zero_touch_namespace,
                exporters=exporters,
                otlp_export_endpoint=otlp_endpoint,
            )
            plan = planner.plan(discovered)
            report["zero_touch"] = _serialize(plan)

    if args.trace:
        try:
            from slo_copilot.copilot import SLOCopilot
        except Exception as exc:
            report["warnings"].append(f"SLO Copilot unavailable: {exc}")
        else:
            copilot = SLOCopilot(enable_caat=True, enable_trag=True, enable_ebpf=True)
            copilot_report = copilot.run(
                trace_path=args.trace,
                telemetry_volumes=_split_floats(args.telemetry_volume),
                expected_signals=args.expected_signal,
                observed_signals=args.observed_signal,
            )
            report["slo_copilot"] = _serialize(copilot_report)
            report["caat"] = _serialize(copilot_report.telemetry_recommendation) if copilot_report.telemetry_recommendation else None
            report["t_rag"] = copilot_report.rca

    _emit(report, args.output)


def _emit(report: Dict[str, Any], output: Optional[str]) -> None:
    payload = json.dumps(report, indent=2)
    if output:
        Path(output).write_text(payload, encoding="utf-8")
    print(payload)


def _split_floats(values: Optional[List[str]]) -> Optional[List[float]]:
    if not values:
        return None
    return [float(value) for value in values]


def _parse_exporters(values: Optional[List[str]]) -> tuple[list[str], Optional[str]]:
    exporters = []
    otlp_endpoint = None
    for value in values or []:
        if value.startswith("otlp="):
            exporters.append("otlp")
            otlp_endpoint = value.split("=", 1)[1]
        else:
            exporters.append(value)
    return exporters or ["logging"], otlp_endpoint


def _serialize(obj):
    if hasattr(obj, "__dict__"):
        return {key: _serialize(value) for key, value in obj.__dict__.items()}
    if isinstance(obj, list):
        return [_serialize(item) for item in obj]
    if isinstance(obj, dict):
        return {key: _serialize(value) for key, value in obj.items()}
    return obj


def _find_repo_root() -> Optional[Path]:
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "projects").is_dir():
            return parent
    return None


def _extend_path(path: Path) -> None:
    import sys

    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


if __name__ == "__main__":
    main()
