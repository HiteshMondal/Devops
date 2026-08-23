"""
Token Bucket rate limiter.

System design concept used to protect API endpoints from being
overwhelmed by a single client. Each client id gets its own bucket
that refills at a constant rate.
"""

from __future__ import annotations

import threading
import time


class TokenBucket:
    def __init__(self, capacity: int, refill_per_minute: int) -> None:
        self.capacity = capacity
        self.refill_rate_per_sec = refill_per_minute / 60.0
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate_per_sec)
        self._last_refill = now

    def try_consume(self, tokens: int = 1) -> bool:
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False


class RateLimiter:
    """Keeps one TokenBucket per client key (e.g. API key, IP address)."""

    def __init__(self, requests_per_minute: int) -> None:
        self.requests_per_minute = requests_per_minute
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def _get_bucket(self, key: str) -> TokenBucket:
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = TokenBucket(self.requests_per_minute, self.requests_per_minute)
                self._buckets[key] = bucket
            return bucket

    def allow(self, key: str) -> bool:
        return self._get_bucket(key).try_consume()