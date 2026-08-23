"""
Deployment planning service.

DSA concept: directed graph + topological sort (Kahn's algorithm using
a queue/BFS approach) to compute a safe deployment order for services
that depend on one another (e.g. 'api' depends on 'db' and 'cache').
A cycle in the dependency graph is invalid and is reported as an
error rather than silently ignored.
"""

from __future__ import annotations

from collections import deque

from src.core.exceptions import CyclicDependencyError
from src.models.deployment import DeploymentPlan


def topological_deploy_order(plan: DeploymentPlan) -> list[str]:
    """Return a valid deployment order (dependencies before dependents).

    Raises CyclicDependencyError if the graph has a cycle.
    """
    services = plan.services
    in_degree: dict[str, int] = {name: 0 for name in services}
    adjacency: dict[str, list[str]] = {name: [] for name in services}

    for name, node in services.items():
        for dep in node.depends_on:
            if dep not in services:
                # Treat an unknown dependency as an implicit external node
                # with in_degree 0 so ordering can still proceed.
                services_missing = dep
                in_degree.setdefault(services_missing, 0)
                adjacency.setdefault(services_missing, [])
            adjacency[dep].append(name)
            in_degree[name] += 1

    queue: deque[str] = deque(sorted(n for n, d in in_degree.items() if d == 0))
    order: list[str] = []

    while queue:
        current = queue.popleft()
        order.append(current)
        for neighbor in sorted(adjacency.get(current, [])):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(order) != len(in_degree):
        remaining = sorted(set(in_degree) - set(order))
        raise CyclicDependencyError(
            f"Cyclic dependency detected among services: {remaining}"
        )

    # Only return services that are actually part of the plan (drop any
    # implicit external placeholders introduced above).
    return [name for name in order if name in services]


def build_plan(plan_id: str, services: dict[str, list[str]]) -> DeploymentPlan:
    """Convenience constructor: {service_name: [dependency, ...]} -> DeploymentPlan."""
    plan = DeploymentPlan(plan_id=plan_id)
    for name, deps in services.items():
        plan.add_service(name, deps)
    return plan