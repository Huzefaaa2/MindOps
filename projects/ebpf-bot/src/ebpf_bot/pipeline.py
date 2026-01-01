# pipeline.py

import logging
import os
import time

from ebpf_bot.coverage_bot import CoverageBot
from ebpf_bot.orchestrator import CoverageOrchestrator
from ebpf_bot.processor import SignalProcessor
from ebpf_bot.store import SignalStore
from opentelemetry import _logs as logs
from opentelemetry import metrics, trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

if os.environ.get("ENABLE_OTLP", "true").lower() == "true":
    resource = Resource(attributes={
        SERVICE_NAME: "ebpf-coverage-bot"
    })
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)

    metric_exporter = OTLPMetricExporter(endpoint="http://localhost:4317", insecure=True)
    metric_reader = PeriodicExportingMetricReader(metric_exporter)
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))

    log_exporter = OTLPLogExporter(endpoint="http://localhost:4317", insecure=True)
    log_provider = LoggerProvider(resource=resource)
    log_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    logs.set_logger_provider(log_provider)

    log_handler = LoggingHandler(level=logging.INFO, logger_provider=log_provider)
    pipeline_logger = logging.getLogger("ebpf_bot")
    if not any(isinstance(h, LoggingHandler) for h in pipeline_logger.handlers):
        pipeline_logger.addHandler(log_handler)
    pipeline_logger.setLevel(logging.INFO)

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)
logger = logging.getLogger("ebpf_bot.pipeline")

class UnifiedPipeline:
    def __init__(self):
        expected_signals = {
            "probe_a": "xdp",
            "probe_b": "tracepoint",
            "probe_c": "kprobe"
        }
        self.agent = CoverageBot(expected_signals)
        self.orchestrator = CoverageOrchestrator()
        self.processor = SignalProcessor()
        self.store = SignalStore()
        self.decision_counter = meter.create_counter("ebpf_bot.decisions")
        self.error_counter = meter.create_counter("ebpf_bot.errors")
        self.decision_latency = meter.create_histogram(
            "ebpf_bot.decision_latency_ms"
        )

    def collect_and_decide(self):
        with tracer.start_as_current_span("unified_pipeline_decision") as span:
            start_time = time.monotonic()
            span_context = trace.get_current_span().get_span_context()
            trace_id = f"{span_context.trace_id:032x}"
            span_id = f"{span_context.span_id:016x}"
            logger.info(
                "Collecting coverage and deciding next probe",
                extra={"trace_id": trace_id, "span_id": span_id},
            )
            try:
                coverage = self.agent.get_coverage()
                span.set_attribute("pipeline.coverage_signals", list(coverage.keys()))
                span.set_attribute("pipeline.coverage_count", len(coverage))
                span.add_event("coverage_received", {"signals": str(list(coverage.keys()))})
                next_probe = self.orchestrator.decide_next_probe(coverage)
                span.set_attribute("pipeline.next_probe", next_probe)
                span.add_event("decision_made", {"next_probe": next_probe})
                self.decision_counter.add(1, {"component": "pipeline"})
                processed = self.processor.process(next_probe)
                self.store.save(next_probe, processed)
                self.store.load(next_probe)
                duration_ms = (time.monotonic() - start_time) * 1000.0
                self.decision_latency.record(duration_ms, {"component": "pipeline"})
                logger.info(
                    "Decision complete for probe",
                    extra={"probe": next_probe, "trace_id": trace_id, "span_id": span_id},
                )
                print(f"[Pipeline] Next probe target: {next_probe}")
                return next_probe
            except Exception as exc:
                self.error_counter.add(1, {"component": "pipeline"})
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR))
                logger.exception(
                    "Pipeline decision failed",
                    extra={"trace_id": trace_id, "span_id": span_id},
                )
                raise
