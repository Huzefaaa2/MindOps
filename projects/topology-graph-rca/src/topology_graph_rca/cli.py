"""CLI for Topology Graph RCA."""
from __future__ import annotations

import argparse
import json
import subprocess
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
    parser.add_argument("--output-svg", help="Write graph SVG to path (requires Graphviz dot)")
    parser.add_argument("--render-svg", help="Write DOT + SVG using the provided base path")
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

    if args.output_dot or args.output_svg or args.render_svg:
        graph = TopologyGraph()
        for node in report.nodes:
            graph.add_node(node)
        for edge in report.edges:
            graph.add_edge(edge)

        if args.render_svg:
            base = Path(args.render_svg)
            dot_path = base.with_suffix(".dot")
            svg_path = base.with_suffix(".svg")
            dot_path.write_text(graph.to_dot(), encoding="utf-8")
            _render_svg(dot_path, svg_path)

        if args.output_dot:
            dot_path = Path(args.output_dot)
            dot_path.write_text(graph.to_dot(), encoding="utf-8")
            if args.output_svg:
                _render_svg(dot_path, Path(args.output_svg))

        if args.output_svg and not args.output_dot and not args.render_svg:
            dot_path = Path(args.output_svg).with_suffix(".dot")
            dot_path.write_text(graph.to_dot(), encoding="utf-8")
            _render_svg(dot_path, Path(args.output_svg))


def _serialize(obj):
    if hasattr(obj, "__dict__"):
        return {key: _serialize(value) for key, value in obj.__dict__.items()}
    if isinstance(obj, list):
        return [_serialize(item) for item in obj]
    if isinstance(obj, dict):
        return {key: _serialize(value) for key, value in obj.items()}
    return obj


def _render_svg(dot_path: Path, svg_path: Path) -> None:
    try:
        subprocess.run(["dot", "-Tsvg", str(dot_path), "-o", str(svg_path)], check=True)
    except FileNotFoundError as exc:
        raise RuntimeError("Graphviz 'dot' not found. Install graphviz to render SVG.") from exc


if __name__ == "__main__":
    main()
