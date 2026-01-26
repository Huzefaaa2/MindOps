#!/usr/bin/env python3
"""Generate synthetic trace samples for the MindOps demo pack."""
from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path


def _span(trace_id: str, span_id: str, parent: str | None, name: str, service: str, start_ns: int, duration_ms: int, status: str = "OK", code: int = 200) -> dict:
    return {
        "traceId": trace_id,
        "spanId": span_id,
        "parentSpanId": parent,
        "name": name,
        "startTimeUnixNano": start_ns,
        "endTimeUnixNano": start_ns + duration_ms * 1_000_000,
        "attributes": [
            {"key": "service.name", "value": {"stringValue": service}},
            {"key": "http.status_code", "value": {"intValue": code}},
        ],
        "status": {"code": status},
    }


def build_flat_trace(seed: int) -> list:
    random.seed(seed)
    base_ns = int(time.time() * 1_000_000_000)
    spans = []
    spans.append(_span("trace-1", "span-1", None, "GET /checkout", "checkout-service", base_ns, 420))
    spans.append(_span("trace-1", "span-2", "span-1", "POST /payment", "payment-service", base_ns + 60_000_000, 520, status="ERROR", code=503))
    spans.append(_span("trace-1", "span-3", "span-2", "POST /fraud-check", "fraud-service", base_ns + 120_000_000, 180))
    spans.append(_span("trace-2", "span-4", None, "GET /catalog", "catalog-service", base_ns + 600_000_000, 260))
    spans.append(_span("trace-2", "span-5", "span-4", "GET /inventory", "inventory-service", base_ns + 680_000_000, 240))
    return spans


def build_otlp_trace(flat_spans: list) -> dict:
    by_service: dict[str, list] = {}
    for span in flat_spans:
        service = "unknown"
        for attr in span.get("attributes", []):
            if attr.get("key") == "service.name":
                service = attr.get("value", {}).get("stringValue", "unknown")
                break
        by_service.setdefault(service, []).append(span)

    resource_spans = []
    for service, spans in by_service.items():
        resource_spans.append(
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": service}}
                    ]
                },
                "scopeSpans": [
                    {
                        "spans": [
                            {
                                "traceId": span["traceId"],
                                "spanId": span["spanId"],
                                **({"parentSpanId": span["parentSpanId"]} if span.get("parentSpanId") else {}),
                                "name": span["name"],
                                "attributes": [
                                    attr for attr in span.get("attributes", []) if attr.get("key") != "service.name"
                                ],
                                "status": span.get("status", {"code": "OK"}),
                            }
                            for span in spans
                        ]
                    }
                ],
            }
        )

    return {"resourceSpans": resource_spans}


def write_payload(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic trace samples.")
    parser.add_argument("--output-dir", default="demos/enterprise-day-zero/out", help="Output directory")
    parser.add_argument("--seed", type=int, default=7, help="Random seed")
    parser.add_argument("--format", choices=["flat", "otlp", "both"], default="both")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    flat = build_flat_trace(args.seed)

    if args.format in ("flat", "both"):
        write_payload(out_dir / "synthetic_trace_flat.json", flat)

    if args.format in ("otlp", "both"):
        otlp = build_otlp_trace(flat)
        write_payload(out_dir / "synthetic_trace_otlp.json", otlp)

    print(f"Wrote traces to {out_dir}")


if __name__ == "__main__":
    main()
