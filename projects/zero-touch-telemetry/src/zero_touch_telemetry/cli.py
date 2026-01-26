"""CLI for Zero-Touch Telemetry."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Optional, Tuple

from .apply import apply_plan_dict
from .discovery import discover_services
from .planner import ZeroTouchPlanner
from .policy import load_sampling_policy


def _parse_exporters(values: Optional[List[str]]) -> Tuple[List[str], Optional[str]]:
    exporters = []
    otlp_endpoint = None
    for value in values or []:
        if value.startswith("otlp="):
            exporters.append("otlp")
            otlp_endpoint = value.split("=", 1)[1]
        else:
            exporters.append(value)
    return exporters or ["logging"], otlp_endpoint


def main() -> None:
    parser = argparse.ArgumentParser(description="Zero-Touch Telemetry for Kubernetes")
    parser.add_argument("--manifests", action="append", required=True, help="Manifest file or directory")
    parser.add_argument("--mode", choices=["auto", "gateway", "daemonset", "sidecar"], default="auto")
    parser.add_argument("--namespace", default="observability")
    parser.add_argument("--exporter", action="append", help="Exporter (logging or otlp=http://host:4317)")
    parser.add_argument("--sampling-rate", type=float, default=1.0)
    parser.add_argument("--policy", help="Optional JSON policy file with sampling_action or sampling_rate")
    parser.add_argument("--output-dir", help="Write plan artifacts to this directory")
    parser.add_argument("--apply", action="store_true", help="Apply manifest and patches via kubectl")
    parser.add_argument("--kubectl", default="kubectl", help="kubectl binary path")
    parser.add_argument("--dry-run", action="store_true", help="Print kubectl commands without executing")
    parser.add_argument("--diff", action="store_true", help="Run kubectl diff before apply")
    parser.add_argument("--diff-only", action="store_true", help="Run kubectl diff and skip apply")
    args = parser.parse_args()

    exporters, otlp_endpoint = _parse_exporters(args.exporter)
    sampling_rate = args.sampling_rate
    if args.policy:
        policy_rate = load_sampling_policy(args.policy)
        if policy_rate is not None:
            sampling_rate = policy_rate

    discovered = discover_services(args.manifests)
    planner = ZeroTouchPlanner(
        mode=args.mode,
        namespace=args.namespace,
        exporters=exporters,
        otlp_export_endpoint=otlp_endpoint,
        sampling_rate=sampling_rate,
    )
    plan = planner.plan(discovered)

    if args.output_dir:
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "collector-config.yaml").write_text(plan.collector.config_yaml, encoding="utf-8")
        (out_dir / "collector-manifest.yaml").write_text(plan.collector.manifest_yaml, encoding="utf-8")
        (out_dir / "plan.json").write_text(json.dumps(_serialize(plan), indent=2), encoding="utf-8")

    if args.apply:
        commands = apply_plan_dict(
            _serialize(plan),
            kubectl=args.kubectl,
            dry_run=args.dry_run,
            diff=args.diff,
            diff_only=args.diff_only,
            output_dir=Path(args.output_dir) if args.output_dir else None,
        )
        if args.dry_run:
            print("\n".join(commands))

    print(json.dumps(_serialize(plan), indent=2))


def _serialize(obj):
    if hasattr(obj, "__dict__"):
        return {key: _serialize(value) for key, value in obj.__dict__.items()}
    if isinstance(obj, list):
        return [_serialize(item) for item in obj]
    if isinstance(obj, dict):
        return {key: _serialize(value) for key, value in obj.items()}
    return obj


if __name__ == "__main__":
    main()
