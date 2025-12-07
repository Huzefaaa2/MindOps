"""
trace_loader.py
================

Utilities for loading and parsing trace data into a form suitable for
vector embedding and retrieval.  T‑RAG treats each span in a trace
as a separate document; this module defines a :class:`SpanRecord`
dataclass representing the essential fields of a span and a
:class:`TraceLoader` class for reading JSON traces from disk.

Trace files are expected to be in a format compatible with
OpenTelemetry JSON exports.  A single trace file typically contains
a list of spans or a nested structure (resourceSpans/scopeSpans) that
can be flattened.  See ``examples/sample_trace.json`` for an example.

If you wish to ingest spans from other sources (e.g. directly from a
Jaeger or Tempo backend), you can extend :class:`TraceLoader` and
override the :meth:`load_raw` method.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Iterable, Any


@dataclass
class SpanRecord:
    """Represents a simplified view of a trace span for embedding.

    Attributes:
        trace_id: Identifier of the trace this span belongs to.
        span_id: Identifier of the span itself.
        parent_id: Identifier of the parent span (if any).
        service_name: Name of the service emitting the span.
        operation: Span name or operation.
        start_time: Start timestamp in ISO‑8601 or epoch milliseconds.
        end_time: End timestamp in ISO‑8601 or epoch milliseconds.
        attributes: Dictionary of span attributes.
        status: Status of the span (e.g. "OK", "ERROR").
        message: Human‑readable string summarizing the span contents.
    """

    trace_id: str
    span_id: str
    parent_id: str | None
    service_name: str
    operation: str
    start_time: Any
    end_time: Any
    attributes: Dict[str, Any]
    status: str
    message: str


class TraceLoader:
    """Loads and processes trace data into :class:`SpanRecord` objects."""

    def __init__(self, source: str | Path) -> None:
        """Initialize the loader.

        Args:
            source: Path to a JSON file containing trace data or a
                directory containing multiple JSON files.  Each file
                should contain a list of spans in OpenTelemetry JSON
                format.  See ``examples/sample_trace.json`` for an
                example schema.
        """
        self.source = Path(source)

    def load_spans(self) -> List[SpanRecord]:
        """Load spans from the configured source.

        Returns:
            A list of :class:`SpanRecord` instances representing all
            successfully parsed spans.  Invalid spans are skipped with
            a warning.
        """
        raw_spans: Iterable[Dict[str, Any]] = self.load_raw()
        records: List[SpanRecord] = []
        for span in raw_spans:
            try:
                record = self._span_to_record(span)
                records.append(record)
            except Exception as exc:
                # Skip spans that cannot be parsed and log a warning
                print(f"Warning: failed to parse span {span}: {exc}")
                continue
        return records

    def load_raw(self) -> Iterable[Dict[str, Any]]:
        """Load raw span dictionaries from the source.

        This method returns an iterable of span dictionaries.  If the
        source is a directory, all ``*.json`` files are iterated over.

        Returns:
            An iterable of raw span dictionaries.
        """
        if self.source.is_dir():
            for file_path in self.source.glob("*.json"):
                yield from self._load_file(file_path)
        else:
            yield from self._load_file(self.source)

    def _load_file(self, file_path: Path) -> Iterable[Dict[str, Any]]:
        """Load spans from a single JSON file."""
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            # If the JSON contains a nested structure, extract spans
            # heuristically.  OpenTelemetry's export format often nests
            # resource spans and scope spans; we flatten them here.
            return self._extract_spans_from_otlp(data)

    def _extract_spans_from_otlp(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract spans from the OTLP collector format.

        OTLP JSON exports typically have the following structure::

            {
              "resourceSpans": [
                {
                  "resource": { ... },
                  "scopeSpans": [
                    {
                      "scope": { ... },
                      "spans": [ ... ]
                    }
                  ]
                }
              ]
            }

        This helper walks through the nested fields and returns a flat
        list of spans.  If no spans are found, an empty list is
        returned.

        Args:
            data: The parsed JSON object from the trace file.

        Returns:
            A list of span dictionaries extracted from the nested
            structure.
        """
        spans: List[Dict[str, Any]] = []
        resource_spans = data.get("resourceSpans", [])
        for res in resource_spans:
            scope_spans = res.get("scopeSpans", [])
            for scope in scope_spans:
                spans.extend(scope.get("spans", []))
        return spans

    def _span_to_record(self, span: Dict[str, Any]) -> SpanRecord:
        """Convert a raw span dictionary into a :class:`SpanRecord`.

        Args:
            span: Raw span dictionary parsed from JSON.

        Returns:
            A :class:`SpanRecord` with fields populated from the raw
            span.  If mandatory keys are missing, an exception will
            propagate to the caller.
        """
        trace_id = span.get("traceId") or span.get("trace_id")
        span_id = span.get("spanId") or span.get("span_id")
        parent_id = span.get("parentSpanId") or span.get("parent_id")
        service_name = self._get_service_name(span)
        operation = span.get("name") or span.get("operationName")
        start_time = span.get("startTimeUnixNano") or span.get("startTime")
        end_time = span.get("endTimeUnixNano") or span.get("endTime")
        attributes = self._get_attributes(span)
        status = self._get_status(span)
        # Compose a succinct human‑readable summary of the span
        message = self._build_message(service_name, operation, attributes, status)
        return SpanRecord(
            trace_id=trace_id,
            span_id=span_id,
            parent_id=parent_id,
            service_name=service_name,
            operation=operation,
            start_time=start_time,
            end_time=end_time,
            attributes=attributes,
            status=status,
            message=message,
        )

    def _get_service_name(self, span: Dict[str, Any]) -> str:
        """Extract the service name from span attributes or resource."""
        # Check attributes first
        for attribute in span.get("attributes", []):
            key = attribute.get("key") or attribute.get("name")
            if key == "service.name":
                value = attribute.get("value")
                if isinstance(value, dict):
                    return value.get("stringValue") or value.get("value") or "unknown_service"
                return value or "unknown_service"
        # Fall back to resource field if present
        resource = span.get("resource") or {}
        for attribute in resource.get("attributes", []):
            key = attribute.get("key") or attribute.get("name")
            if key == "service.name":
                value = attribute.get("value")
                if isinstance(value, dict):
                    return value.get("stringValue") or value.get("value") or "unknown_service"
                return value or "unknown_service"
        return "unknown_service"

    def _get_attributes(self, span: Dict[str, Any]) -> Dict[str, Any]:
        """Extract attributes from the span into a flat dictionary."""
        attrs: Dict[str, Any] = {}
        for attribute in span.get("attributes", []):
            key = attribute.get("key") or attribute.get("name")
            value = attribute.get("value")
            # OTLP attributes wrap values in type containers
            if isinstance(value, dict):
                value = next(iter(value.values()))
            attrs[key] = value
        return attrs

    def _get_status(self, span: Dict[str, Any]) -> str:
        """Derive a simple status string from the span."""
        status = span.get("status", {})
        return status.get("message") or status.get("code") or "OK"

    def _build_message(
        self,
        service_name: str,
        operation: str,
        attributes: Dict[str, Any],
        status: str,
    ) -> str:
        """Construct a human‑readable summary of a span.

        The summary concatenates selected fields into a single string
        that is suitable for feeding into an embedding model.  By
        default it includes the service name, operation and status,
        along with a handful of commonly interesting attributes (HTTP
        method, URL and exception message).  You can adjust the list
        of interesting attributes to match your instrumentation.

        Args:
            service_name: Name of the service emitting the span.
            operation: Name or operation of the span.
            attributes: Dictionary of span attributes.
            status: Status string for the span.

        Returns:
            A semicolon‑delimited string summarising the span.
        """
        parts = [
            f"service: {service_name}",
            f"operation: {operation}",
            f"status: {status}",
        ]
        # Limit the number of attributes included to keep the message concise
        interesting_keys = ["http.method", "http.url", "exception.message"]
        for key in interesting_keys:
            if key in attributes:
                parts.append(f"{key}: {attributes[key]}")
        return "; ".join(parts)