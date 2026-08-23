"""
Log lookup service.

DSA concept: binary search (via the `bisect` module) over a
timestamp-sorted list of log entries. This lets us answer "give me
logs from resource X at/after time T" in O(log n) instead of scanning
every log entry linearly, which matters once a resource has
accumulated a large log history.
"""

from __future__ import annotations

from bisect import bisect_left
from typing import Any


class LogIndex:
    """Wraps a chronologically sorted list of log rows for fast lookups.

    Each row is expected to be a dict with at least a 'timestamp' key
    (ISO-8601 strings sort lexicographically the same as chronologically).
    """

    def __init__(self, sorted_logs: list[dict[str, Any]]) -> None:
        self._logs = sorted_logs
        self._timestamps = [row["timestamp"] for row in sorted_logs]

    def find_from(self, timestamp: str) -> list[dict[str, Any]]:
        """Return all log entries with timestamp >= the given timestamp."""
        idx = bisect_left(self._timestamps, timestamp)
        return self._logs[idx:]

    def find_before(self, timestamp: str) -> list[dict[str, Any]]:
        """Return all log entries with timestamp < the given timestamp."""
        idx = bisect_left(self._timestamps, timestamp)
        return self._logs[:idx]

    def __len__(self) -> int:
        return len(self._logs)