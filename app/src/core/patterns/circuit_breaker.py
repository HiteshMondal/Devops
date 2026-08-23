"""
Circuit Breaker pattern.

System design concept used to protect the system from repeatedly
calling a failing dependency (e.g. an unhealthy server or database).

States: CLOSED -> OPEN -> HALF_OPEN -> CLOSED
- CLOSED:    calls pass through normally.
- OPEN:      calls fail fast without executing, until reset timeout elapses.
- HALF_OPEN: a single trial call is allowed through to probe recovery.
"""

from __future__ import annotations

import enum
import threading
import time
from typing import Callable, TypeVar

from src.core.exceptions import CircuitOpenError

T = TypeVar("T")


class CircuitState(str, enum.Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, reset_seconds: int = 30) -> None:
        self.failure_threshold = failure_threshold
        self.reset_seconds = reset_seconds
        self._failure_count = 0
        self._state = CircuitState.CLOSED
        self._opened_at: float | None = None
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            self._maybe_half_open()
            return self._state

    def _maybe_half_open(self) -> None:
        if (
            self._state == CircuitState.OPEN
            and self._opened_at is not None
            and (time.monotonic() - self._opened_at) >= self.reset_seconds
        ):
            self._state = CircuitState.HALF_OPEN

    def call(self, func: Callable[[], T]) -> T:
        with self._lock:
            self._maybe_half_open()
            if self._state == CircuitState.OPEN:
                raise CircuitOpenError("Circuit breaker is OPEN; call rejected")

        try:
            result = func()
        except Exception:
            self._on_failure()
            raise
        else:
            self._on_success()
            return result

    def _on_success(self) -> None:
        with self._lock:
            self._failure_count = 0
            self._state = CircuitState.CLOSED
            self._opened_at = None

    def _on_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()