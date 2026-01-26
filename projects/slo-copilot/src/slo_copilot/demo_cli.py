"""Minimal CLI demo for CAAT + eBPF integrations."""
from __future__ import annotations

import argparse
import json
from typing import List, Optional

from .copilot import SLOCopilot


def _split_floats(values: Optional[List[str]]) -> Optional[List[float]]:
    if not values:
        return None
    return [float(value) for value in values]


def main() -> None:
    parser = argparse.ArgumentParser(description="SLO Copilot CAAT + eBPF demo")
    parser.add_argument("--trace", required=True, help="Path to a trace JSON file")
    parser.add_argument("--telemetry-volume", action="append", help="Telemetry volume sample (repeatable)")
    parser.add_argument("--expected-signal", action="append", help="Expected eBPF signal name")
    parser.add_argument("--observed-signal", action="append", help="Observed signal name")
    args = parser.parse_args()

    copilot = SLOCopilot(enable_caat=True, enable_trag=False, enable_ebpf=True)

    report = copilot.run(
        trace_path=args.trace,
        telemetry_volumes=_split_floats(args.telemetry_volume),
        expected_signals=args.expected_signal or ["probe_a", "probe_b", "probe_c"],
        observed_signals=args.observed_signal,
    )

    output = {
        "coverage": report.coverage.__dict__ if report.coverage else None,
        "telemetry_recommendation": report.telemetry_recommendation.__dict__ if report.telemetry_recommendation else None,
        "integration_status": report.integrations,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
