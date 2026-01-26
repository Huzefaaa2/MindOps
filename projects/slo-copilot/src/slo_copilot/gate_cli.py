"""CLI for running the deployment gate stub."""
from __future__ import annotations

import argparse
import json
from typing import List, Optional

from .copilot import SLOCopilot
from .deployment_gate import gate_from_report
from .trace_stats import compute_trace_stats


def _split_floats(values: Optional[List[str]]) -> Optional[List[float]]:
    if not values:
        return None
    return [float(value) for value in values]


def main() -> None:
    parser = argparse.ArgumentParser(description="SLO Copilot Deployment Gate Stub")
    parser.add_argument("--trace", required=True, help="Path to a trace JSON file")
    parser.add_argument("--telemetry-volume", action="append", help="Telemetry volume sample (repeatable)")
    parser.add_argument("--expected-signal", action="append", help="Expected eBPF signal name")
    parser.add_argument("--observed-signal", action="append", help="Observed signal name")
    parser.add_argument("--disable-caat", action="store_true", help="Disable CAAT integration")
    parser.add_argument("--disable-trag", action="store_true", help="Disable T-RAG integration")
    parser.add_argument("--disable-ebpf", action="store_true", help="Disable eBPF-bot integration")
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

    spans = copilot._load_spans(args.trace)
    stats = compute_trace_stats(spans)
    decision = gate_from_report(report, stats)

    print(json.dumps({
        "passed": decision.passed,
        "failures": decision.failures,
        "results": decision.results,
    }, indent=2))


if __name__ == "__main__":
    main()
