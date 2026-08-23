"""
Infrastructure resource models.

OOP concepts demonstrated:
- Abstraction: `Resource` is an abstract base class defining a contract.
- Inheritance: `Server`, `Container`, `Database` extend `Resource`.
- Polymorphism: each subclass implements `health_check()` and
  `describe()` differently, but callers can treat them uniformly
  through the `Resource` interface.
- Encapsulation: internal state (`_status`) is only mutated through
  methods, not touched directly by callers.
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class ResourceStatus(str, enum.Enum):
    UNKNOWN = "UNKNOWN"
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"


@dataclass
class Resource(ABC):
    """Abstract base class for any manageable infrastructure resource."""

    resource_id: str
    name: str
    _status: ResourceStatus = field(default=ResourceStatus.UNKNOWN, repr=False)

    @property
    def status(self) -> ResourceStatus:
        return self._status

    @abstractmethod
    def health_check(self) -> ResourceStatus:
        """Run a health check and update/return the resource status."""
        raise NotImplementedError

    @abstractmethod
    def describe(self) -> str:
        """Return a short human-readable description of this resource."""
        raise NotImplementedError

    def mark_status(self, status: ResourceStatus) -> None:
        self._status = status


@dataclass
class Server(Resource):
    cpu_cores: int = 1
    memory_gb: int = 1
    region: str = "local"

    def health_check(self) -> ResourceStatus:
        # Simplified deterministic health rule: a server with 0 cores is down.
        status = ResourceStatus.DOWN if self.cpu_cores <= 0 else ResourceStatus.HEALTHY
        self.mark_status(status)
        return status

    def describe(self) -> str:
        return (
            f"Server(id={self.resource_id}, name={self.name}, "
            f"cores={self.cpu_cores}, mem={self.memory_gb}GB, region={self.region})"
        )


@dataclass
class Container(Resource):
    image: str = "unknown:latest"
    replicas: int = 1

    def health_check(self) -> ResourceStatus:
        status = ResourceStatus.HEALTHY if self.replicas > 0 else ResourceStatus.DEGRADED
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
        ratio = self.connections / self.max_connections if self.max_connections else 1.0
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
            f"engine={self.engine}, connections={self.connections}/{self.max_connections})"
        )