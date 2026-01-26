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
    parser.add_argument("--zero-touch-apply", action="store_true", help="Apply Zero-Touch plan via kubectl")
    parser.add_argument("--zero-touch-diff-only", action="store_true", help="Run kubectl diff only for Zero-Touch plan")
    parser.add_argument("--kubectl", default="kubectl", help="kubectl binary path for Zero-Touch apply")
    parser.add_argument("--export-dir", help="Write structured report artifacts to this directory")
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

    zero_touch_plan = None
    if args.manifests:
        try:
            from zero_touch_telemetry.discovery import discover_services
            from zero_touch_telemetry.planner import ZeroTouchPlanner
            from zero_touch_telemetry.apply import apply_plan_dict
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
            zero_touch_plan = _serialize(plan)
            report["zero_touch"] = zero_touch_plan
            if args.zero_touch_apply or args.zero_touch_diff_only:
                commands = apply_plan_dict(
                    zero_touch_plan,
                    kubectl=args.kubectl,
                    diff_only=args.zero_touch_diff_only,
                    diff=True,
                    output_dir=Path(args.export_dir) if args.export_dir else None,
                )
                report["zero_touch_apply"] = {"commands": commands, "diff_only": args.zero_touch_diff_only}

    slo_report = None
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
            slo_report = _serialize(copilot_report)
            report["slo_copilot"] = slo_report
            report["caat"] = _serialize(copilot_report.telemetry_recommendation) if copilot_report.telemetry_recommendation else None
            report["t_rag"] = copilot_report.rca

    if args.export_dir:
        _export_structured(
            Path(args.export_dir),
            report=report,
            zero_touch=zero_touch_plan,
            slo_report=slo_report,
        )

    _emit(report, args.output)


def _emit(report: Dict[str, Any], output: Optional[str]) -> None:
    payload = json.dumps(report, indent=2)
    if output:
        Path(output).write_text(payload, encoding="utf-8")
    print(payload)


def _export_structured(base: Path, report: Dict[str, Any], zero_touch: Optional[Dict[str, Any]], slo_report: Optional[Dict[str, Any]]) -> None:
    base.mkdir(parents=True, exist_ok=True)
    (base / "orchestrator_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if zero_touch:
        ztt_dir = base / "zero_touch"
        ztt_dir.mkdir(parents=True, exist_ok=True)
        (ztt_dir / "plan.json").write_text(json.dumps(zero_touch, indent=2), encoding="utf-8")
        manifest = zero_touch.get("collector", {}).get("manifest_yaml")
        config = zero_touch.get("collector", {}).get("config_yaml")
        if manifest:
            (ztt_dir / "collector-manifest.yaml").write_text(manifest, encoding="utf-8")
        if config:
            (ztt_dir / "collector-config.yaml").write_text(config, encoding="utf-8")
    if slo_report:
        slo_dir = base / "slo_copilot"
        slo_dir.mkdir(parents=True, exist_ok=True)
        (slo_dir / "report.json").write_text(json.dumps(slo_report, indent=2), encoding="utf-8")


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
