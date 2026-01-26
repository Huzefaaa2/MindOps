"""All-in-one demo: CAAT + eBPF + exports + deployment gate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Optional

from .copilot import SLOCopilot
from .deployment_gate import gate_from_report
from .exports import export_open_slo, export_slo_json
from .openslo_yaml import export_open_slo_yaml
from .trace_stats import compute_trace_stats


def _split_floats(values: Optional[List[str]]) -> Optional[List[float]]:
    if not values:
        return None
    return [float(value) for value in values]


def _write_json(payload, path: Path) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="SLO Copilot all-in-one demo")
    parser.add_argument("--trace", required=True, help="Path to a trace JSON file")
    parser.add_argument("--telemetry-volume", action="append", help="Telemetry volume sample (repeatable)")
    parser.add_argument("--expected-signal", action="append", help="Expected eBPF signal name")
    parser.add_argument("--observed-signal", action="append", help="Observed signal name")
    parser.add_argument("--export-dir", default="exports", help="Directory to write export JSON files")
    args = parser.parse_args()

    copilot = SLOCopilot(enable_caat=True, enable_trag=False, enable_ebpf=True)

    report = copilot.run(
        trace_path=args.trace,
        telemetry_volumes=_split_floats(args.telemetry_volume),
        expected_signals=args.expected_signal or ["probe_a", "probe_b", "probe_c"],
        observed_signals=args.observed_signal,
    )

    spans = copilot._load_spans(args.trace)
    stats = compute_trace_stats(spans)
    gate_decision = gate_from_report(report, stats)

    export_dir = Path(args.export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    slo_export_path = export_dir / "slo_export.json"
    openslo_export_path = export_dir / "openslo.json"
    openslo_yaml_path = export_dir / "openslo.yaml"
    _write_json(export_slo_json(report.slo_candidates), slo_export_path)
    _write_json(export_open_slo(report.slo_candidates), openslo_export_path)
    openslo_yaml_path.write_text(export_open_slo_yaml(report.slo_candidates), encoding="utf-8")

    output = {
        "coverage": report.coverage.__dict__ if report.coverage else None,
        "telemetry_recommendation": report.telemetry_recommendation.__dict__ if report.telemetry_recommendation else None,
        "gate": {
            "passed": gate_decision.passed,
            "failures": gate_decision.failures,
            "results": gate_decision.results,
        },
        "exports": {
            "slo_export": str(slo_export_path),
            "openslo_export": str(openslo_export_path),
            "openslo_yaml": str(openslo_yaml_path),
        },
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
