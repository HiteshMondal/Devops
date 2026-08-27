"""System Design fundamentals.

Small, dependency-free reference implementations of patterns that show up
constantly in backend/platform work: rate limiting, caching, resilience,
partitioning, and load balancing.
"""
from __future__ import annotations

import bisect
import hashlib
import time
from collections import OrderedDict
from enum import Enum
from typing import Hashable


# -- Rate Limiter

class TokenBucketRateLimiter:
    """Classic token-bucket rate limiter (smooths bursts)."""

    def __init__(self, capacity: int, refill_per_second: float):
        self.capacity = capacity
        self.refill_per_second = refill_per_second
        self._tokens = float(capacity)
        self._last_check = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_check
        self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_per_second)
        self._last_check = now

    def allow(self, cost: int = 1) -> bool:
        self._refill()
        if self._tokens >= cost:
            self._tokens -= cost
            return True
        return False


# --- LRU Cache

class LRUCache:
    """Fixed-capacity cache evicting the Least Recently Used entry."""

    def __init__(self, capacity: int):
        self.capacity = capacity
        self._store: OrderedDict[Hashable, object] = OrderedDict()

    def get(self, key: Hashable):
        if key not in self._store:
            return None
        self._store.move_to_end(key)
        return self._store[key]

    def put(self, key: Hashable, value: object) -> None:
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = value
        if len(self._store) > self.capacity:
            self._store.popitem(last=False)  # evict LRU

    def __len__(self) -> int:
        return len(self._store)


# --- Circuit Breaker

class CircuitState(str, Enum):
    CLOSED = "closed"      # requests flow normally
    OPEN = "open"           # failing fast, no requests allowed
    HALF_OPEN = "half_open"  # trial request allowed to test recovery


class CircuitBreaker:
    """Stops calling a failing dependency until it recovers."""

    def __init__(self, failure_threshold: int = 5, reset_timeout_seconds: float = 30):
        self.failure_threshold = failure_threshold
        self.reset_timeout_seconds = reset_timeout_seconds
        self._failures = 0
        self._state = CircuitState.CLOSED
        self._opened_at: float | None = None

    @property
    def state(self) -> CircuitState:
        if (
            self._state == CircuitState.OPEN
            and self._opened_at is not None
            and time.monotonic() - self._opened_at >= self.reset_timeout_seconds
        ):
            self._state = CircuitState.HALF_OPEN
        return self._state

    def allow_request(self) -> bool:
        return self.state != CircuitState.OPEN

    def record_success(self) -> None:
        self._failures = 0
        self._state = CircuitState.CLOSED
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.failure_threshold:
            self._state = CircuitState.OPEN
            self._opened_at = time.monotonic()


#  Consistent Hashing

class ConsistentHashRing:
    """Maps keys to nodes with minimal remapping when nodes change."""

    def __init__(self, nodes: list[str] | None = None, virtual_replicas: int = 100):
        self.virtual_replicas = virtual_replicas
        self._ring: dict[int, str] = {}
        self._sorted_hashes: list[int] = []
        for node in nodes or []:
            self.add_node(node)

    @staticmethod
    def _hash(key: str) -> int:
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def add_node(self, node: str) -> None:
        for i in range(self.virtual_replicas):
            h = self._hash(f"{node}#{i}")
            self._ring[h] = node
            bisect.insort(self._sorted_hashes, h)

    def remove_node(self, node: str) -> None:
        for i in range(self.virtual_replicas):
            h = self._hash(f"{node}#{i}")
            self._ring.pop(h, None)
            idx = bisect.bisect_left(self._sorted_hashes, h)
            if idx < len(self._sorted_hashes) and self._sorted_hashes[idx] == h:
                self._sorted_hashes.pop(idx)

    def get_node(self, key: str) -> str | None:
        if not self._ring:
            return None
        h = self._hash(key)
        idx = bisect.bisect(self._sorted_hashes, h) % len(self._sorted_hashes)
        return self._ring[self._sorted_hashes[idx]]


#  Load Balancer

class RoundRobinBalancer:
    """Distributes requests evenly across a fixed pool of backends."""

    def __init__(self, backends: list[str]):
        if not backends:
            raise ValueError("RoundRobinBalancer requires at least one backend")
        self._backends = backends
        self._index = 0

    def next_backend(self) -> str:
        backend = self._backends[self._index % len(self._backends)]
        self._index += 1
        return backend