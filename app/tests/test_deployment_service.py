import pytest

from src.core.exceptions import CyclicDependencyError
from src.services.deployment_service import build_plan, topological_deploy_order


def test_topological_order_respects_dependencies():
    plan = build_plan(
        "plan-1",
        {
            "api": ["db", "cache"],
            "db": [],
            "cache": [],
            "worker": ["api"],
        },
    )
    order = topological_deploy_order(plan)

    assert order.index("db") < order.index("api")
    assert order.index("cache") < order.index("api")
    assert order.index("api") < order.index("worker")
    assert set(order) == {"api", "db", "cache", "worker"}


def test_cycle_raises_error():
    plan = build_plan(
        "plan-2",
        {
            "a": ["b"],
            "b": ["a"],
        },
    )
    with pytest.raises(CyclicDependencyError):
        topological_deploy_order(plan)


def test_independent_services_all_included():
    plan = build_plan("plan-3", {"a": [], "b": [], "c": []})
    order = topological_deploy_order(plan)
    assert set(order) == {"a", "b", "c"}