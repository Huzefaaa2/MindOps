"""CI gate for SLO Copilot."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from .copilot import SLOCopilot
from .deployment_gate import gate_from_report
from .trace_stats import compute_trace_stats


def main() -> None:
    parser = argparse.ArgumentParser(description="SLO Copilot CI Gate")
    parser.add_argument("--trace", required=True, help="Path to trace JSON")
    parser.add_argument("--telemetry-volume", action="append", help="Telemetry volume sample")
    parser.add_argument("--expected-signal", action="append")
    parser.add_argument("--observed-signal", action="append")
    parser.add_argument("--fail-on", choices=["any", "baseline", "tests", "guardrail"], default="any")
    parser.add_argument("--disable-caat", action="store_true")
    parser.add_argument("--disable-trag", action="store_true")
    parser.add_argument("--disable-ebpf", action="store_true")
    parser.add_argument("--json-output", help="Write summary JSON to path")
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

    baseline_failures = [eval_item for eval_item in report.baseline_evaluations if not eval_item.passed]
    test_failures = [
        evaluation
        for result in report.test_results
        for evaluation in result.evaluations
        if not evaluation.passed
    ]

    spans = copilot._load_spans(args.trace)
    stats = compute_trace_stats(spans)
    guardrail = gate_from_report(report, stats)

    summary = {
        "baseline_failures": len(baseline_failures),
        "test_failures": len(test_failures),
        "guardrail_passed": guardrail.passed,
    }

    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)

    should_fail = _should_fail(args.fail_on, baseline_failures, test_failures, guardrail)
    if should_fail:
        print(json.dumps(summary, indent=2))
        sys.exit(1)
    print(json.dumps(summary, indent=2))


def _split_floats(values: Optional[List[str]]) -> Optional[List[float]]:
    if not values:
        return None
    return [float(value) for value in values]


def _should_fail(choice: str, baseline, tests, guardrail) -> bool:
    if choice == "baseline":
        return len(baseline) > 0
    if choice == "tests":
        return len(tests) > 0
    if choice == "guardrail":
        return not guardrail.passed
    return len(baseline) > 0 or len(tests) > 0 or not guardrail.passed


if __name__ == "__main__":
    main()
