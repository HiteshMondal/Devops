import time

import pytest

from src.config import CircuitOpenError, CyclicDependencyError
from src.models import Container, Database, Resource, ResourceStatus, Server, Task
from src.services import (
    CircuitBreaker,
    CircuitState,
    LogIndex,
    LRUCache,
    MonitoringService,
    RateLimiter,
    TaskScheduler,
    build_plan,
    topological_deploy_order,
)


# Resource models (OOP: abstraction, inheritance, polymorphism)


def test_server_health_check_healthy_with_cores():
    server = Server(resource_id="s1", name="web-1", cpu_cores=2)
    assert server.health_check() == ResourceStatus.HEALTHY
    assert server.status == ResourceStatus.HEALTHY


def test_server_health_check_down_with_no_cores():
    server = Server(resource_id="s2", name="web-2", cpu_cores=0)
    assert server.health_check() == ResourceStatus.DOWN


def test_container_health_check_degraded_with_zero_replicas():
    container = Container(resource_id="c1", name="api", replicas=0)
    assert container.health_check() == ResourceStatus.DEGRADED


def test_database_model_health_check_thresholds():
    healthy_db = Database(resource_id="d1", name="pg", connections=10, max_connections=100)
    degraded_db = Database(resource_id="d2", name="pg", connections=85, max_connections=100)
    down_db = Database(resource_id="d3", name="pg", connections=100, max_connections=100)

    assert healthy_db.health_check() == ResourceStatus.HEALTHY
    assert degraded_db.health_check() == ResourceStatus.DEGRADED
    assert down_db.health_check() == ResourceStatus.DOWN


def test_polymorphism_via_common_interface():
    resources: list[Resource] = [
        Server(resource_id="s1", name="web", cpu_cores=4),
        Container(resource_id="c1", name="api", replicas=3),
        Database(resource_id="d1", name="pg", connections=5, max_connections=100),
    ]
    statuses = [r.health_check() for r in resources]
    assert all(isinstance(s, ResourceStatus) for s in statuses)
    assert all(isinstance(r.describe(), str) for r in resources)


# Deployment service (topological sort)


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


# Circuit breaker / rate limiter (system design patterns)


def test_circuit_breaker_opens_after_threshold():
    breaker = CircuitBreaker(failure_threshold=2, reset_seconds=60)

    def failing():
        raise RuntimeError("boom")

    for _ in range(2):
        with pytest.raises(RuntimeError):
            breaker.call(failing)

    assert breaker.state == CircuitState.OPEN
    with pytest.raises(CircuitOpenError):
        breaker.call(lambda: "should not run")


def test_circuit_breaker_half_opens_after_reset():
    breaker = CircuitBreaker(failure_threshold=1, reset_seconds=1)

    def failing():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        breaker.call(failing)

    assert breaker.state == CircuitState.OPEN

    time.sleep(1.01)

    result = breaker.call(lambda: "recovered")

    assert result == "recovered"
    assert breaker.state == CircuitState.CLOSED


def test_rate_limiter_allows_up_to_capacity_then_blocks():
    limiter = RateLimiter(requests_per_minute=3)
    key = "client-1"
    assert limiter.allow(key) is True
    assert limiter.allow(key) is True
    assert limiter.allow(key) is True
    assert limiter.allow(key) is False


def test_rate_limiter_tracks_separate_clients_independently():
    limiter = RateLimiter(requests_per_minute=1)
    assert limiter.allow("client-a") is True
    assert limiter.allow("client-b") is True
    assert limiter.allow("client-a") is False


# Log service (binary search)

SAMPLE_LOGS = [
    {"timestamp": "2026-01-01T00:00:00", "message": "one"},
    {"timestamp": "2026-01-01T00:05:00", "message": "two"},
    {"timestamp": "2026-01-01T00:10:00", "message": "three"},
    {"timestamp": "2026-01-01T00:15:00", "message": "four"},
]


def test_find_from_returns_matching_and_later_entries():
    index = LogIndex(SAMPLE_LOGS)
    result = index.find_from("2026-01-01T00:10:00")
    assert [r["message"] for r in result] == ["three", "four"]


def test_find_before_returns_earlier_entries():
    index = LogIndex(SAMPLE_LOGS)
    result = index.find_before("2026-01-01T00:10:00")
    assert [r["message"] for r in result] == ["one", "two"]


def test_find_from_timestamp_before_all_entries_returns_all():
    index = LogIndex(SAMPLE_LOGS)
    assert len(index.find_from("2025-01-01T00:00:00")) == len(SAMPLE_LOGS)


def test_find_from_timestamp_after_all_entries_returns_empty():
    index = LogIndex(SAMPLE_LOGS)
    assert index.find_from("2027-01-01T00:00:00") == []


# Monitoring service (LRU cache)


def test_lru_cache_evicts_least_recently_used():
    cache = LRUCache[str, int](capacity=2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.get("a")  # touch 'a' so 'b' becomes least-recently-used
    cache.put("c", 3)  # should evict 'b'
    assert cache.get("a") == 1
    assert cache.get("b") is None
    assert cache.get("c") == 3


def test_lru_cache_rejects_non_positive_capacity():
    with pytest.raises(ValueError):
        LRUCache(capacity=0)


def test_monitoring_service_records_and_reads_status():
    service = MonitoringService(capacity=10)
    service.record_status("server-1", "HEALTHY")
    assert service.get_cached_status("server-1") == "HEALTHY"
    assert service.get_cached_status("unknown") is None


# Task scheduler (priority queue)


def test_pop_next_returns_highest_priority_first():
    scheduler = TaskScheduler()
    scheduler.submit(Task(name="low", priority=9))
    scheduler.submit(Task(name="urgent", priority=0))
    scheduler.submit(Task(name="medium", priority=5))

    first = scheduler.pop_next()
    second = scheduler.pop_next()
    third = scheduler.pop_next()
    assert [first.name, second.name, third.name] == ["urgent", "medium", "low"]


def test_equal_priority_is_fifo():
    scheduler = TaskScheduler()
    scheduler.submit(Task(name="a", priority=3))
    scheduler.submit(Task(name="b", priority=3))
    assert scheduler.pop_next().name == "a"
    assert scheduler.pop_next().name == "b"


def test_pop_next_on_empty_queue_returns_none():
    scheduler = TaskScheduler()
    assert scheduler.pop_next() is None


def test_len_reflects_pending_count():
    scheduler = TaskScheduler()
    scheduler.submit(Task(name="a", priority=1))
    scheduler.submit(Task(name="b", priority=2))
    assert len(scheduler) == 2
    scheduler.pop_next()
    assert len(scheduler) == 1