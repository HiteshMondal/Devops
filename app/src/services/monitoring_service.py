"""
Monitoring service.

DSA concept: LRU (Least Recently Used) cache, implemented with
`OrderedDict` for O(1) get/put. Used to cache recent health-check
results for resources so repeated status lookups (e.g. from a
dashboard polling every few seconds) don't have to recompute or
re-fetch the health check every time, while bounding memory use by
evicting the least-recently-used entries once capacity is reached.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class LRUCache(Generic[K, V]):
    def __init__(self, capacity: int = 128) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._store: "OrderedDict[K, V]" = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: K) -> V | None:
        with self._lock:
            if key not in self._store:
                return None
            self._store.move_to_end(key)
            return self._store[key]

    def put(self, key: K, value: V) -> None:
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = value
            if len(self._store) > self.capacity:
                self._store.popitem(last=False)  # evict least-recently-used

    def __contains__(self, key: K) -> bool:
        with self._lock:
            return key in self._store

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)


class MonitoringService:
    """Caches health-check results for resources using an LRU cache."""

    def __init__(self, capacity: int = 128) -> None:
        self._cache: LRUCache[str, str] = LRUCache(capacity=capacity)

    def record_status(self, resource_id: str, status: str) -> None:
        self._cache.put(resource_id, status)

    def get_cached_status(self, resource_id: str) -> str | None:
        return self._cache.get(resource_id)

    def cache_size(self) -> int:
        return len(self._cache)