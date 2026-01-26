"""CLI for Topology Graph RCA."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Optional

from .analyzer import TopologyAnalyzer
from .graph import TopologyGraph


def main() -> None:
    parser = argparse.ArgumentParser(description="Topology Graph RCA")
    parser.add_argument("--manifests", action="append", help="Manifest file or directory")
    parser.add_argument("--traces", action="append", help="Trace JSON file")
    parser.add_argument("--error-threshold", type=float, default=0.05)
    parser.add_argument("--output", help="Write report JSON to path")
    parser.add_argument("--output-dot", help="Write graph DOT to path")
    args = parser.parse_args()

    analyzer = TopologyAnalyzer(error_threshold=args.error_threshold)
    report = analyzer.analyze(
        manifest_paths=args.manifests,
        trace_paths=args.traces,
    )

    payload = _serialize(report)
    if args.output:
        Path(args.output).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))

    if args.output_dot:
        graph = TopologyGraph()
        for node in report.nodes:
            graph.add_node(node)
        for edge in report.edges:
            graph.add_edge(edge)
        Path(args.output_dot).write_text(graph.to_dot(), encoding="utf-8")


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
