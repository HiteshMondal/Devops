import os

import pytest

from src.core.config import Settings
from src.db.database import Database
from src.db.repository import DeploymentRepository, ServerRepository, TaskRepository


@pytest.fixture()
def temp_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(db_file))
    Settings.reset()
    Database.reset()
    yield Database()
    Database.reset()
    Settings.reset()


def test_server_repository_upsert_and_get(temp_db):
    repo = ServerRepository(db=temp_db)
    repo.upsert("s1", "web-1", 4, 8, "us-east", "HEALTHY")

    row = repo.get("s1")
    assert row["name"] == "web-1"
    assert row["cpu_cores"] == 4
    assert row["status"] == "HEALTHY"

    # Upsert again should update, not duplicate.
    repo.upsert("s1", "web-1-renamed", 4, 8, "us-east", "DEGRADED")
    rows = repo.list_all()
    assert len(rows) == 1
    assert rows[0]["name"] == "web-1-renamed"
    assert rows[0]["status"] == "DEGRADED"


def test_task_repository_create_and_list(temp_db):
    repo = TaskRepository(db=temp_db)
    task_id = repo.create("restart-service", priority=1)
    repo.create("run-backup", priority=5)

    tasks = repo.list_all()
    assert len(tasks) == 2
    assert tasks[0]["name"] == "restart-service"  # lowest priority first

    repo.update_status(task_id, "DONE")
    tasks = repo.list_all()
    assert any(t["id"] == task_id and t["status"] == "DONE" for t in tasks)


def test_deployment_repository_save_and_get_plan(temp_db):
    repo = DeploymentRepository(db=temp_db)
    repo.save_plan("plan-1", {"api": ["db"], "db": []})

    services = repo.get_plan("plan-1")
    deps = repo.get_dependencies("plan-1")

    assert {s["service_name"] for s in services} == {"api", "db"}
    assert len(deps) == 1
    assert deps[0]["service_name"] == "api"
    assert deps[0]["depends_on_service"] == "db"