import logging
import pathlib
import sys
import time

from opentelemetry import _logs as logs
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

project_root = pathlib.Path(__file__).resolve().parents[1]
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from ebpf_bot.pipeline import UnifiedPipeline


def configure_telemetry() -> None:
    resource = Resource(attributes={SERVICE_NAME: "ebpf-coverage-bot"})

    trace_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
    trace_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(trace_provider)

    metric_exporter = OTLPMetricExporter(endpoint="http://localhost:4317", insecure=True)
    metric_reader = PeriodicExportingMetricReader(metric_exporter)
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))

    log_exporter = OTLPLogExporter(endpoint="http://localhost:4317", insecure=True)
    log_provider = LoggerProvider(resource=resource)
    log_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    logs.set_logger_provider(log_provider)

    handler = LoggingHandler(level=logging.INFO, logger_provider=log_provider)
    logging.getLogger("ebpf_bot").addHandler(handler)
    logging.getLogger("ebpf_bot").setLevel(logging.INFO)


def emit_metrics_and_logs() -> None:
    meter = metrics.get_meter(__name__)
    counter = meter.create_counter("ebpf_bot.events")
    counter.add(1, {"component": "emit_telemetry"})

    logger = logging.getLogger("ebpf_bot")
    logger.info("emit_telemetry run complete", extra={"event": "telemetry_emitted"})


def main() -> None:
    configure_telemetry()
    UnifiedPipeline().collect_and_decide()
    emit_metrics_and_logs()
    time.sleep(2)


if __name__ == "__main__":
    main()
