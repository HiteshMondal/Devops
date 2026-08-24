"""
Application configuration and shared infrastructure utilities.

This module intentionally contains configuration plus small supporting
patterns because the project uses a flat src/ layout.
"""

from __future__ import annotations

import enum
import logging
import os
import sys
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar


# Configuration

@dataclass
class _SettingsData:
    app_name: str = "devops-console"
    env: str = field(default_factory=lambda: os.getenv("APP_ENV", "local"))
    db_path: str = field(default_factory=lambda: os.getenv("DB_PATH", "app.db"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    max_concurrent_deployments: int = field(
        default_factory=lambda: int(os.getenv("MAX_CONCURRENT_DEPLOYMENTS", "3"))
    )
    rate_limit_per_minute: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    )
    lru_cache_size: int = field(
        default_factory=lambda: int(os.getenv("LRU_CACHE_SIZE", "128"))
    )
    circuit_breaker_failure_threshold: int = field(
        default_factory=lambda: int(os.getenv("CB_FAILURE_THRESHOLD", "5"))
    )
    circuit_breaker_reset_seconds: int = field(
        default_factory=lambda: int(os.getenv("CB_RESET_SECONDS", "30"))
    )


class Settings:
    """Thread-safe Singleton wrapper around _SettingsData."""

    _instance: "Settings | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "Settings":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._data = _SettingsData()
                    cls._instance = instance
        return cls._instance

    def __getattr__(self, item: str) -> Any:
        return getattr(self._data, item)

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            cls._instance = None


def get_settings() -> Settings:
    return Settings()


# Exceptions

class AppError(Exception):
    """Base class for application errors."""


class NotFoundError(AppError):
    pass


class ValidationError(AppError):
    pass


class CyclicDependencyError(AppError):
    pass


class CircuitOpenError(AppError):
    pass


class RateLimitExceededError(AppError):
    pass


# Logging

_CONFIGURED = False


def configure_logging() -> None:
    global _CONFIGURED

    if _CONFIGURED:
        return

    settings = get_settings()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )

    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())
    root.handlers.clear()
    root.addHandler(handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)


# Circuit Breaker

T = TypeVar("T")


class CircuitState(str, enum.Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_seconds: int = 30,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.reset_seconds = reset_seconds
        self._failure_count = 0
        self._state = CircuitState.CLOSED
        self._opened_at: float | None = None
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            return self._state

    def _maybe_half_open(self) -> None:
        if (
            self._state == CircuitState.OPEN
            and self._opened_at is not None
            and time.monotonic() - self._opened_at >= self.reset_seconds
        ):
            self._state = CircuitState.HALF_OPEN

    def call(self, func: Callable[[], T]) -> T:
        with self._lock:
            self._maybe_half_open()

            if self._state == CircuitState.OPEN:
                raise CircuitOpenError(
                    "Circuit breaker is OPEN; call rejected"
                )

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


# Observer

class Observer(ABC):
    @abstractmethod
    def update(self, event: str, payload: dict[str, Any]) -> None:
        raise NotImplementedError


class Subject:
    def __init__(self) -> None:
        self._observers: list[Observer] = []

    def attach(self, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(
        self,
        event: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        for observer in self._observers:
            observer.update(event, payload or {})


class LoggingObserver(Observer):
    def __init__(self) -> None:
        self._logger = get_logger("events")

    def update(self, event: str, payload: dict[str, Any]) -> None:
        self._logger.info("event=%s payload=%s", event, payload)


class InMemoryAlertObserver(Observer):
    def __init__(self) -> None:
        self.alerts: list[dict[str, Any]] = []

    def update(self, event: str, payload: dict[str, Any]) -> None:
        self.alerts.append({
            "event": event,
            "payload": payload,
        })

    def latest(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.alerts[-limit:]


# Token Bucket Rate Limiter

class TokenBucket:
    def __init__(
        self,
        capacity: int,
        refill_per_minute: int,
    ) -> None:
        self.capacity = capacity
        self.refill_rate_per_sec = refill_per_minute / 60.0
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill

        self._tokens = min(
            self.capacity,
            self._tokens + elapsed * self.refill_rate_per_sec,
        )

        self._last_refill = now

    def try_consume(self, tokens: int = 1) -> bool:
        with self._lock:
            self._refill()

            if self._tokens >= tokens:
                self._tokens -= tokens
                return True

            return False


class RateLimiter:
    def __init__(self, requests_per_minute: int) -> None:
        self.requests_per_minute = requests_per_minute
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def _get_bucket(self, key: str) -> TokenBucket:
        with self._lock:
            bucket = self._buckets.get(key)

            if bucket is None:
                bucket = TokenBucket(
                    self.requests_per_minute,
                    self.requests_per_minute,
                )
                self._buckets[key] = bucket

            return bucket

    def allow(self, key: str) -> bool:
        return self._get_bucket(key).try_consume()