from __future__ import annotations

import pytest

from src.config import Settings
from src.database import (
    Database,
    DeploymentRepository,
    LogRepository,
    ServerRepository,
    TaskRepository,
)


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Point the Database singleton at a fresh temp file for every test."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    Settings.reset()
    Database.reset()
    yield
    Database.reset()
    Settings.reset()


def test_server_repository_upsert_and_get():
    repo = ServerRepository()
    repo.upsert("s1", "web-1", 2, 4, "us-east", "HEALTHY")

    row = repo.get("s1")
    assert row is not None
    assert row["name"] == "web-1"
    assert row["status"] == "HEALTHY"

    # Upsert again with a new status should update, not duplicate.
    repo.upsert("s1", "web-1", 2, 4, "us-east", "DEGRADED")
    rows = repo.list_all()
    assert len(rows) == 1
    assert rows[0]["status"] == "DEGRADED"


def test_task_repository_create_and_list():
    repo = TaskRepository()
    task_id = repo.create("run-backup", priority=1)
    repo.update_status(task_id, "DONE")

    rows = repo.list_all()
    assert len(rows) == 1
    assert rows[0]["status"] == "DONE"


def test_deployment_repository_save_and_get_plan():
    repo = DeploymentRepository()
    repo.save_plan("plan-1", {"api": ["db"], "db": []})

    services = repo.get_plan("plan-1")
    deps = repo.get_dependencies("plan-1")

    assert {s["service_name"] for s in services} == {"api", "db"}
    assert len(deps) == 1
    assert deps[0]["service_name"] == "api"
    assert deps[0]["depends_on_service"] == "db"


def test_log_repository_sorted_listing():
    repo = LogRepository()
    repo.add("res-1", "INFO", "first")
    repo.add("res-1", "ERROR", "second")

    rows = repo.list_for_resource_sorted("res-1")
    assert [r["message"] for r in rows] == ["first", "second"]