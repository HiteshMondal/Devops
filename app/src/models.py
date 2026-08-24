"""
Application domain models.

All models live in this single module because this project intentionally
uses a flat src/ layout.
"""

from __future__ import annotations

import enum
import itertools
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


# Deployment models

class DeploymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass
class ServiceNode:
    name: str
    depends_on: list[str] = field(default_factory=list)
    status: DeploymentStatus = DeploymentStatus.PENDING


@dataclass
class DeploymentPlan:
    plan_id: str
    services: dict[str, ServiceNode] = field(default_factory=dict)

    def add_service(
        self,
        name: str,
        depends_on: list[str] | None = None,
    ) -> None:
        self.services[name] = ServiceNode(
            name=name,
            depends_on=depends_on or [],
        )


# Resource models

class ResourceStatus(str, enum.Enum):
    UNKNOWN = "UNKNOWN"
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"


@dataclass
class Resource(ABC):
    resource_id: str
    name: str
    _status: ResourceStatus = field(
        default=ResourceStatus.UNKNOWN,
        repr=False,
    )

    @property
    def status(self) -> ResourceStatus:
        return self._status

    @abstractmethod
    def health_check(self) -> ResourceStatus:
        raise NotImplementedError

    @abstractmethod
    def describe(self) -> str:
        raise NotImplementedError

    def mark_status(self, status: ResourceStatus) -> None:
        self._status = status


@dataclass
class Server(Resource):
    cpu_cores: int = 1
    memory_gb: int = 1
    region: str = "local"

    def health_check(self) -> ResourceStatus:
        status = (
            ResourceStatus.DOWN
            if self.cpu_cores <= 0
            else ResourceStatus.HEALTHY
        )
        self.mark_status(status)
        return status

    def describe(self) -> str:
        return (
            f"Server(id={self.resource_id}, name={self.name}, "
            f"cores={self.cpu_cores}, mem={self.memory_gb}GB, "
            f"region={self.region})"
        )


@dataclass
class Container(Resource):
    image: str = "unknown:latest"
    replicas: int = 1

    def health_check(self) -> ResourceStatus:
        status = (
            ResourceStatus.HEALTHY
            if self.replicas > 0
            else ResourceStatus.DEGRADED
        )
        self.mark_status(status)
        return status

    def describe(self) -> str:
        return (
            f"Container(id={self.resource_id}, name={self.name}, "
            f"image={self.image}, replicas={self.replicas})"
        )


@dataclass
class Database(Resource):
    engine: str = "postgres"
    connections: int = 0
    max_connections: int = 100

    def health_check(self) -> ResourceStatus:
        ratio = (
            self.connections / self.max_connections
            if self.max_connections
            else 1.0
        )

        if ratio >= 1.0:
            status = ResourceStatus.DOWN
        elif ratio >= 0.8:
            status = ResourceStatus.DEGRADED
        else:
            status = ResourceStatus.HEALTHY

        self.mark_status(status)
        return status

    def describe(self) -> str:
        return (
            f"Database(id={self.resource_id}, name={self.name}, "
            f"engine={self.engine}, "
            f"connections={self.connections}/{self.max_connections})"
        )


# Task models

_id_counter = itertools.count(1)


class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


@dataclass
class Task:
    name: str
    priority: int
    task_id: int = field(
        default_factory=lambda: next(_id_counter)
    )
    status: TaskStatus = TaskStatus.PENDING

    def __repr__(self) -> str:
        return (
            f"Task(id={self.task_id}, "
            f"name={self.name!r}, "
            f"priority={self.priority}, "
            f"status={self.status})"
        )