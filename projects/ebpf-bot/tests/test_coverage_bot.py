from ebpf_bot.coverage_bot import CoverageBot

def test_find_missing_signals():
    # Prepare example expected and observed signals
    expected = ["metric1", "metric2", "traceA"]
    observed = ["metric1", "traceA"]
    bot = CoverageBot(expected)
    missing = bot.find_missing_signals(observed)
    # Only "metric2" is missing since metric1 and traceA are observed
    assert missing == ["metric2"]

def test_suggest_instrumentation():
    bot = CoverageBot(expected_signals=[])
    missing_signals = ["metricX", "traceY"]
    suggestions = bot.suggest_instrumentation(missing_signals)
    # Should suggest adding eBPF probes for each missing signal
    assert suggestions == ["Add eBPF probe for 'metricX'", "Add eBPF probe for 'traceY'"]
