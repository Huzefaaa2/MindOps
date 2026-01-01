import os
import sys

import pytest
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider


def test_pipeline_emits_decision_metrics():
    metric_reader = pytest.importorskip(
        "opentelemetry.sdk.metrics.export",
        reason="Metrics SDK export helpers not available",
    )
    InMemoryMetricReader = getattr(metric_reader, "InMemoryMetricReader", None)
    if InMemoryMetricReader is None:
        pytest.skip("InMemoryMetricReader not available in this SDK version")

    reader = InMemoryMetricReader()
    metrics.set_meter_provider(MeterProvider(metric_readers=[reader]))

    old_enable_otlp = os.environ.get("ENABLE_OTLP")
    os.environ["ENABLE_OTLP"] = "false"

    if "ebpf_bot.pipeline" in sys.modules:
        del sys.modules["ebpf_bot.pipeline"]

    from ebpf_bot.pipeline import UnifiedPipeline

    pipeline = UnifiedPipeline()
    pipeline.collect_and_decide()

    data = reader.get_metrics_data()
    metric_names = {
        metric.name
        for resource in data.resource_metrics
        for scope in resource.scope_metrics
        for metric in scope.metrics
    }

    assert "ebpf_bot.decisions" in metric_names
    assert "ebpf_bot.decision_latency_ms" in metric_names

    if old_enable_otlp is not None:
        os.environ["ENABLE_OTLP"] = old_enable_otlp
    else:
        os.environ.pop("ENABLE_OTLP", None)
