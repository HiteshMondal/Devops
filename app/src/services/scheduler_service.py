"""
Task scheduler service.

DSA concept: Priority Queue implemented with a binary heap (`heapq`).
Used to decide which DevOps task (e.g. restart a service, run a
backup, roll out a patch) should run next, favoring lower priority
numbers (0 = most urgent).
"""

from __future__ import annotations

import heapq
import itertools
import threading

from src.models.task import Task, TaskStatus


class TaskScheduler:
    """A thread-safe priority queue wrapper for Task objects.

    Internally stores tuples of (priority, sequence, task) on a heap.
    The sequence counter is a tie-breaker so tasks with equal priority
    are still comparable and processed in FIFO order (stable
    scheduling), and so heapq never has to compare Task objects
    directly.
    """

    def __init__(self) -> None:
        self._heap: list[tuple[int, int, Task]] = []
        self._counter = itertools.count()
        self._lock = threading.Lock()

    def submit(self, task: Task) -> None:
        with self._lock:
            heapq.heappush(self._heap, (task.priority, next(self._counter), task))

    def pop_next(self) -> Task | None:
        """Pop and return the highest-priority (lowest number) pending task."""
        with self._lock:
            if not self._heap:
                return None
            _, _, task = heapq.heappop(self._heap)
            task.status = TaskStatus.RUNNING
            return task

    def peek_next(self) -> Task | None:
        with self._lock:
            if not self._heap:
                return None
            return self._heap[0][2]

    def __len__(self) -> int:
        with self._lock:
            return len(self._heap)

    def all_pending(self) -> list[Task]:
        """Return pending tasks ordered by priority without mutating the heap."""
        with self._lock:
            return [t for _, _, t in sorted(self._heap)]