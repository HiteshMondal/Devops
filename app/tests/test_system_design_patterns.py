import time

import pytest

from src.core.exceptions import CircuitOpenError
from src.core.patterns.circuit_breaker import CircuitBreaker, CircuitState
from src.core.patterns.rate_limiter import RateLimiter


def test_circuit_breaker_opens_after_threshold():
    breaker = CircuitBreaker(failure_threshold=2, reset_seconds=60)

    def failing():
        raise RuntimeError("boom")

    for _ in range(2):
        with pytest.raises(RuntimeError):
            breaker.call(failing)

    assert breaker.state == CircuitState.OPEN
    with pytest.raises(CircuitOpenError):
        breaker.call(lambda: "should not run")


def test_circuit_breaker_half_opens_after_reset(monkeypatch):
    breaker = CircuitBreaker(failure_threshold=1, reset_seconds=0)

    def failing():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        breaker.call(failing)
    assert breaker.state == CircuitState.OPEN

    time.sleep(0.01)
    assert breaker.state == CircuitState.HALF_OPEN

    result = breaker.call(lambda: "recovered")
    assert result == "recovered"
    assert breaker.state == CircuitState.CLOSED


def test_rate_limiter_allows_up_to_capacity_then_blocks():
    limiter = RateLimiter(requests_per_minute=3)
    key = "client-1"
    assert limiter.allow(key) is True
    assert limiter.allow(key) is True
    assert limiter.allow(key) is True
    assert limiter.allow(key) is False


def test_rate_limiter_tracks_separate_clients_independently():
    limiter = RateLimiter(requests_per_minute=1)
    assert limiter.allow("client-a") is True
    assert limiter.allow("client-b") is True
    assert limiter.allow("client-a") is False