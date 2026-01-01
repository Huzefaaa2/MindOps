# test_orchestrator.py

from ebpf_bot.orchestrator import CoverageOrchestrator

def test_decide_next_probe():
    orchestrator = CoverageOrchestrator()
    data = {"probe_a": False, "probe_b": True}
    assert orchestrator.decide_next_probe(data) == "probe_a"
