"""
Application services.

Contains:
- deployment graph/topological sorting
- circuit breaker
- observer pattern
- health service
- binary-search log index
- LRU cache
- monitoring service
- token bucket rate limiter
- priority queue task scheduler
"""

from __future__ import annotations

import enum
import heapq
import itertools
import threading
import time
from bisect import bisect_left
from collections import OrderedDict, deque
from typing import Any, Callable, Generic, TypeVar

from src.config import (
    CircuitOpenError,
    CyclicDependencyError,
)
from src.models import (
    DeploymentPlan,
    Resource,
    ResourceStatus,
    Task,
    TaskStatus,
)


# Circuit breaker

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
            self._maybe_half_open()
            return self._state

    def _maybe_half_open(self) -> None:
        if (
            self._state == CircuitState.OPEN
            and self._opened_at is not None
            and (
                time.monotonic() - self._opened_at
                >= self.reset_seconds
            )
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


# Observer pattern

class Observer:
    def update(
        self,
        event: str,
        payload: dict[str, Any],
    ) -> None:
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


class InMemoryAlertObserver(Observer):
    def __init__(self) -> None:
        self.alerts: list[dict[str, Any]] = []

    def update(
        self,
        event: str,
        payload: dict[str, Any],
    ) -> None:
        self.alerts.append(
            {
                "event": event,
                "payload": payload,
            }
        )

    def latest(
        self,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        return self.alerts[-limit:]


# Deployment graph / topological sorting

def topological_deploy_order(
    plan: DeploymentPlan,
) -> list[str]:
    """
    Return dependencies before dependents.

    Uses Kahn's algorithm.
    """

    services = plan.services

    in_degree: dict[str, int] = {
        name: 0
        for name in services
    }

    adjacency: dict[str, list[str]] = {
        name: []
        for name in services
    }

    for name, node in services.items():
        for dep in node.depends_on:

            if dep not in services:
                in_degree.setdefault(dep, 0)
                adjacency.setdefault(dep, [])

            adjacency[dep].append(name)
            in_degree[name] += 1

    queue: deque[str] = deque(
        sorted(
            name
            for name, degree in in_degree.items()
            if degree == 0
        )
    )

    order: list[str] = []

    while queue:
        current = queue.popleft()
        order.append(current)

        for neighbor in sorted(
            adjacency.get(current, [])
        ):
            in_degree[neighbor] -= 1

            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(order) != len(in_degree):
        remaining = sorted(
            set(in_degree) - set(order)
        )

        raise CyclicDependencyError(
            "Cyclic dependency detected among services: "
            f"{remaining}"
        )

    return [
        name
        for name in order
        if name in services
    ]


def build_plan(
    plan_id: str,
    services: dict[str, list[str]],
) -> DeploymentPlan:
    plan = DeploymentPlan(plan_id=plan_id)

    for name, dependencies in services.items():
        plan.add_service(
            name,
            dependencies,
        )

    return plan


# Health service

class HealthService(Subject):

    def __init__(
        self,
        failure_threshold: int = 5,
        reset_seconds: int = 30,
    ) -> None:
        super().__init__()

        self._breakers: dict[
            str,
            CircuitBreaker,
        ] = {}

        self._failure_threshold = failure_threshold
        self._reset_seconds = reset_seconds

    def _breaker_for(
        self,
        resource_id: str,
    ) -> CircuitBreaker:

        if resource_id not in self._breakers:
            self._breakers[resource_id] = CircuitBreaker(
                failure_threshold=self._failure_threshold,
                reset_seconds=self._reset_seconds,
            )

        return self._breakers[resource_id]

    def check(
        self,
        resource: Resource,
    ) -> ResourceStatus:

        breaker = self._breaker_for(
            resource.resource_id
        )

        def run_check() -> ResourceStatus:
            status = resource.health_check()

            if status == ResourceStatus.DOWN:
                raise RuntimeError(
                    f"{resource.resource_id} reported DOWN"
                )

            return status

        try:
            status = breaker.call(run_check)

        except CircuitOpenError:
            self.notify(
                "circuit_open",
                {
                    "resource_id": resource.resource_id,
                    "name": resource.name,
                },
            )

            return ResourceStatus.DOWN

        except RuntimeError:
            self.notify(
                "health_check_failed",
                {
                    "resource_id": resource.resource_id,
                    "name": resource.name,
                },
            )

            return ResourceStatus.DOWN

        else:
            self.notify(
                "health_check_ok",
                {
                    "resource_id": resource.resource_id,
                    "status": status.value,
                },
            )

            return status


# Log binary search

class LogIndex:

    def __init__(
        self,
        sorted_logs: list[dict[str, Any]],
    ) -> None:

        self._logs = sorted_logs

        self._timestamps = [
            row["timestamp"]
            for row in sorted_logs
        ]

    def find_from(
        self,
        timestamp: str,
    ) -> list[dict[str, Any]]:

        index = bisect_left(
            self._timestamps,
            timestamp,
        )

        return self._logs[index:]

    def find_before(
        self,
        timestamp: str,
    ) -> list[dict[str, Any]]:

        index = bisect_left(
            self._timestamps,
            timestamp,
        )

        return self._logs[:index]

    def __len__(self) -> int:
        return len(self._logs)


# LRU cache

K = TypeVar("K")
V = TypeVar("V")


class LRUCache(Generic[K, V]):

    def __init__(
        self,
        capacity: int = 128,
    ) -> None:

        if capacity <= 0:
            raise ValueError(
                "capacity must be positive"
            )

        self.capacity = capacity

        self._store: OrderedDict[K, V] = OrderedDict()
        self._lock = threading.Lock()

    def get(
        self,
        key: K,
    ) -> V | None:

        with self._lock:
            if key not in self._store:
                return None

            self._store.move_to_end(key)

            return self._store[key]

    def put(
        self,
        key: K,
        value: V,
    ) -> None:

        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)

            self._store[key] = value

            if len(self._store) > self.capacity:
                self._store.popitem(
                    last=False
                )

    def __contains__(
        self,
        key: K,
    ) -> bool:

        with self._lock:
            return key in self._store

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)


class MonitoringService:

    def __init__(
        self,
        capacity: int = 128,
    ) -> None:

        self._cache = LRUCache[str, str](
            capacity=capacity
        )

    def record_status(
        self,
        resource_id: str,
        status: str,
    ) -> None:

        self._cache.put(
            resource_id,
            status,
        )

    def get_cached_status(
        self,
        resource_id: str,
    ) -> str | None:

        return self._cache.get(resource_id)

    def cache_size(self) -> int:
        return len(self._cache)


# Token bucket

class TokenBucket:

    def __init__(
        self,
        capacity: int,
        refill_per_minute: int,
    ) -> None:

        self.capacity = capacity

        self.refill_rate_per_sec = (
            refill_per_minute / 60.0
        )

        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:

        now = time.monotonic()

        elapsed = (
            now - self._last_refill
        )

        self._tokens = min(
            self.capacity,
            self._tokens
            + elapsed * self.refill_rate_per_sec,
        )

        self._last_refill = now

    def try_consume(
        self,
        tokens: int = 1,
    ) -> bool:

        with self._lock:
            self._refill()

            if self._tokens >= tokens:
                self._tokens -= tokens
                return True

            return False


class RateLimiter:

    def __init__(
        self,
        requests_per_minute: int,
    ) -> None:

        self.requests_per_minute = (
            requests_per_minute
        )

        self._buckets: dict[
            str,
            TokenBucket,
        ] = {}

        self._lock = threading.Lock()

    def _get_bucket(
        self,
        key: str,
    ) -> TokenBucket:

        with self._lock:

            bucket = self._buckets.get(key)

            if bucket is None:
                bucket = TokenBucket(
                    self.requests_per_minute,
                    self.requests_per_minute,
                )

                self._buckets[key] = bucket

            return bucket

    def allow(
        self,
        key: str,
    ) -> bool:

        return self._get_bucket(
            key
        ).try_consume()


# Priority queue scheduler

class TaskScheduler:

    def __init__(self) -> None:

        self._heap: list[
            tuple[int, int, Task]
        ] = []

        self._counter = itertools.count()
        self._lock = threading.Lock()

    def submit(
        self,
        task: Task,
    ) -> None:

        with self._lock:
            heapq.heappush(
                self._heap,
                (
                    task.priority,
                    next(self._counter),
                    task,
                ),
            )

    def pop_next(
        self,
    ) -> Task | None:

        with self._lock:

            if not self._heap:
                return None

            _, _, task = heapq.heappop(
                self._heap
            )

            task.status = TaskStatus.RUNNING

            return task

    def peek_next(
        self,
    ) -> Task | None:

        with self._lock:

            if not self._heap:
                return None

            return self._heap[0][2]

    def __len__(self) -> int:

        with self._lock:
            return len(self._heap)

    def all_pending(self) -> list[Task]:

        with self._lock:
            return [
                task
                for _, _, task
                in sorted(self._heap)
            ]