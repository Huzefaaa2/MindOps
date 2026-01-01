# test_pipeline.py

from ebpf_bot.pipeline import UnifiedPipeline

def test_pipeline_decision_flow():
    pipeline = UnifiedPipeline()
    next_probe = pipeline.collect_and_decide()
    assert next_probe is not None
