"""
Observer pattern.

Used to broadcast infrastructure events (deployment finished, health
check failed, circuit opened, etc.) to any number of interested
listeners (loggers, alert notifiers, metrics collectors) without
coupling the publisher to concrete subscriber implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Observer(ABC):
    """Abstract subscriber."""

    @abstractmethod
    def update(self, event: str, payload: dict[str, Any]) -> None:
        raise NotImplementedError


class Subject:
    """Publisher that maintains a list of observers and notifies them."""

    def __init__(self) -> None:
        self._observers: list[Observer] = []

    def attach(self, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, event: str, payload: dict[str, Any] | None = None) -> None:
        for observer in self._observers:
            observer.update(event, payload or {})


class LoggingObserver(Observer):
    """Concrete observer that writes events to the application logger."""

    def __init__(self) -> None:
        from src.core.logging_config import get_logger

        self._logger = get_logger("events")

    def update(self, event: str, payload: dict[str, Any]) -> None:
        self._logger.info("event=%s payload=%s", event, payload)


class InMemoryAlertObserver(Observer):
    """Concrete observer that accumulates alerts in memory (e.g. for API display)."""

    def __init__(self) -> None:
        self.alerts: list[dict[str, Any]] = []

    def update(self, event: str, payload: dict[str, Any]) -> None:
        self.alerts.append({"event": event, "payload": payload})

    def latest(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.alerts[-limit:]