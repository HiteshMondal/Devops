"""
Health check orchestration service.

Wires together the Circuit Breaker (core.patterns.circuit_breaker) and
the Observer pattern (core.patterns.observer) with the OOP resource
models so a failing resource stops being hammered with checks and
interested parties are notified of state changes.
"""

from __future__ import annotations

from src.core.exceptions import CircuitOpenError
from src.core.patterns.circuit_breaker import CircuitBreaker
from src.core.patterns.observer import Subject
from src.models.resource import Resource, ResourceStatus


class HealthService(Subject):
    def __init__(self, failure_threshold: int = 5, reset_seconds: int = 30) -> None:
        super().__init__()
        self._breakers: dict[str, CircuitBreaker] = {}
        self._failure_threshold = failure_threshold
        self._reset_seconds = reset_seconds

    def _breaker_for(self, resource_id: str) -> CircuitBreaker:
        if resource_id not in self._breakers:
            self._breakers[resource_id] = CircuitBreaker(
                failure_threshold=self._failure_threshold,
                reset_seconds=self._reset_seconds,
            )
        return self._breakers[resource_id]

    def check(self, resource: Resource) -> ResourceStatus:
        breaker = self._breaker_for(resource.resource_id)

        def _run() -> ResourceStatus:
            status = resource.health_check()
            if status == ResourceStatus.DOWN:
                raise RuntimeError(f"{resource.resource_id} reported DOWN")
            return status

        try:
            status = breaker.call(_run)
        except CircuitOpenError:
            self.notify(
                "circuit_open",
                {"resource_id": resource.resource_id, "name": resource.name},
            )
            return ResourceStatus.DOWN
        except RuntimeError:
            self.notify(
                "health_check_failed",
                {"resource_id": resource.resource_id, "name": resource.name},
            )
            return ResourceStatus.DOWN
        else:
            self.notify(
                "health_check_ok",
                {"resource_id": resource.resource_id, "status": status.value},
            )
            return status