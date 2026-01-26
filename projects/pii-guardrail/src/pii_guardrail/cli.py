"""CLI for PII Guardrail."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Optional

from .models import ScrubReport
from .scrubber import PIIScrubber, ScrubberConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="PII Guardrail Pre-Ingest")
    parser.add_argument("--input", required=True, help="Input file (json, jsonl, or text)")
    parser.add_argument("--output", help="Output file (defaults to stdout)")
    parser.add_argument("--format", choices=["auto", "json", "jsonl", "text", "trace"], default="auto")
    parser.add_argument("--redaction-token", default="[REDACTED]")
    parser.add_argument("--enabled-label", action="append", help="Enable specific labels (repeatable)")
    parser.add_argument("--report", help="Write redaction report JSON to path")
    args = parser.parse_args()

    path = Path(args.input)
    fmt = _resolve_format(args.format, path)

    config = ScrubberConfig(
        redaction_token=args.redaction_token,
        enabled_labels=args.enabled_label,
    )
    scrubber = PIIScrubber(config=config)

    if fmt == "text":
        text = path.read_text(encoding="utf-8")
        result = scrubber.scrub_text(text)
        output = result.redacted
        report = _build_report(len(text.splitlines()), result.matches)
    elif fmt == "jsonl":
        records = _load_jsonl(path)
        redacted, report = scrubber.scrub_records(records)
        output = "\n".join(json.dumps(item) for item in redacted)
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
        redacted, report, _matches = scrubber.scrub_object(data)
        output = json.dumps(redacted, indent=2)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)

    if args.report:
        Path(args.report).write_text(json.dumps(report.__dict__, indent=2), encoding="utf-8")


def _resolve_format(fmt: str, path: Path) -> str:
    if fmt != "auto":
        return fmt
    if path.suffix.lower() == ".jsonl":
        return "jsonl"
    if path.suffix.lower() == ".json":
        return "json"
    return "text"


def _load_jsonl(path: Path) -> List[object]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))
    return records


def _build_report(total_fields: int, matches) -> ScrubReport:
    by_label = {}
    for match in matches:
        by_label[match.label] = by_label.get(match.label, 0) + 1
    return ScrubReport(total_fields=total_fields, total_redactions=len(matches), by_label=by_label)


if __name__ == "__main__":
    main()
