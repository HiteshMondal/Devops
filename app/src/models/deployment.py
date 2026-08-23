"""Deployment models representing services and their dependency graph."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field


class DeploymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass
class ServiceNode:
    """A single deployable service and the services it depends on."""

    name: str
    depends_on: list[str] = field(default_factory=list)
    status: DeploymentStatus = DeploymentStatus.PENDING


@dataclass
class DeploymentPlan:
    """A collection of services forming a dependency graph to deploy."""

    plan_id: str
    services: dict[str, ServiceNode] = field(default_factory=dict)

    def add_service(self, name: str, depends_on: list[str] | None = None) -> None:
        self.services[name] = ServiceNode(name=name, depends_on=depends_on or [])