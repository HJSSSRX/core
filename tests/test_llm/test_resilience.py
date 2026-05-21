from forhacker.llm.resilience import ResilienceWrapper


def test_resilience_wrapper_initial_state():
    rw = ResilienceWrapper(max_retries=3, timeout=60.0)
    assert rw._max_retries == 3
    assert rw._circuit_open_until == 0.0
