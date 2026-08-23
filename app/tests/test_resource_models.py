from src.models.resource import Container, Database, Resource, ResourceStatus, Server


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


def test_database_health_check_thresholds():
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