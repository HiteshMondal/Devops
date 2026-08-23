"""Task model used by the scheduler service (see services/scheduler_service.py)."""

from __future__ import annotations

import enum
import itertools
from dataclasses import dataclass, field

_id_counter = itertools.count(1)


class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


@dataclass
class Task:
    """A unit of work to be scheduled, e.g. 'restart-service', 'run-backup'."""

    name: str
    priority: int  # lower number = higher priority
    task_id: int = field(default_factory=lambda: next(_id_counter))
    status: TaskStatus = TaskStatus.PENDING

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"Task(id={self.task_id}, name={self.name!r}, priority={self.priority}, status={self.status})"