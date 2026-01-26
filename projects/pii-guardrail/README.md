# PII Guardrail Pre-Ingest

Project 6 provides a privacy guardrail that redacts sensitive data before logs and traces
enter observability pipelines. It uses pattern-based detection (email, SSN, phone, credit card,
API keys, IPv4) and emits a redaction report to help teams meet compliance requirements.

## What this project delivers

- Regex-based PII detection with Luhn validation for credit cards.
- Recursive scrubbing for JSON logs, OTLP-style traces, and raw text.
- CLI to redact data and emit a redaction report.
- Extensible ruleset (enable/disable labels).

## Directory structure

```
projects/pii-guardrail/
├── README.md
├── examples/
│   ├── sample_logs.jsonl
│   └── sample_trace.json
├── src/
│   └── pii_guardrail/
│       ├── __init__.py
│       ├── cli.py
│       ├── models.py
│       ├── patterns.py
│       └── scrubber.py
└── tests/
    └── test_scrubber.py
```

## Quickstart

From `projects/pii-guardrail`:

```bash
PYTHONPATH=src python3 -m pii_guardrail.cli \
  --input examples/sample_logs.jsonl \
  --format jsonl \
  --output out_logs.jsonl \
  --report redaction_report.json
```

Scrub a trace JSON:

```bash
PYTHONPATH=src python3 -m pii_guardrail.cli \
  --input examples/sample_trace.json \
  --format trace \
  --output out_trace.json
```

Limit to a subset of labels:

```bash
PYTHONPATH=src python3 -m pii_guardrail.cli \
  --input examples/sample_logs.jsonl \
  --format jsonl \
  --enabled-label email \
  --enabled-label ssn
```

## Integration notes

### Zero-Touch Telemetry (Project 5)
Insert PII Guardrail before telemetry export. Use the CLI or embed `PIIScrubber`
within a log/trace forwarding sidecar.

### T-RAG (Project 2)
Redact sensitive payloads before traces are embedded or sent to LLMs.

### SLO Copilot (Project 4)
Use PII Guardrail in the SLO pipeline to prevent sensitive data from appearing
in generated reports.

## Next steps

- Add ML-based detectors (entity recognition) for names and addresses.
- Provide an OpenTelemetry Collector processor extension.
- Add format-preserving tokenization for analytics-friendly redaction.
