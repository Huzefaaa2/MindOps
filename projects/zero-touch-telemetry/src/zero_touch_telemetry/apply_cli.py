"""CLI to apply a saved Zero-Touch plan."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .apply import apply_plan_dict


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply Zero-Touch Telemetry plan")
    parser.add_argument("--plan", required=True, help="Path to plan.json")
    parser.add_argument("--kubectl", default="kubectl")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--diff", action="store_true", help="Run kubectl diff before apply")
    parser.add_argument("--output-dir", help="Optional output dir for manifest")
    args = parser.parse_args()

    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    output_dir = Path(args.output_dir) if args.output_dir else None
    commands = apply_plan_dict(
        plan,
        kubectl=args.kubectl,
        dry_run=args.dry_run,
        diff=args.diff,
        output_dir=output_dir,
    )
    if args.dry_run:
        print("\n".join(commands))


if __name__ == "__main__":
    main()
