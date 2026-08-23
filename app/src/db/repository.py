"""
Repository pattern.

Each repository encapsulates the SQL for one entity type so services
never write raw SQL directly. This keeps SQL centralized, testable,
and swappable (e.g. SQLite today, Postgres later) without touching
business logic.
"""

from __future__ import annotations

from typing import Any

from src.db.database import Database, get_db


class ServerRepository:
    def __init__(self, db: Database | None = None) -> None:
        self._db = db or get_db()

    def upsert(self, server_id: str, name: str, cpu_cores: int, memory_gb: int, region: str, status: str) -> None:
        with self._db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO servers (id, name, cpu_cores, memory_gb, region, status)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    cpu_cores=excluded.cpu_cores,
                    memory_gb=excluded.memory_gb,
                    region=excluded.region,
                    status=excluded.status
                """,
                (server_id, name, cpu_cores, memory_gb, region, status),
            )

    def get(self, server_id: str) -> dict[str, Any] | None:
        with self._db.cursor() as cur:
            cur.execute("SELECT * FROM servers WHERE id = ?", (server_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def list_all(self) -> list[dict[str, Any]]:
        with self._db.cursor() as cur:
            cur.execute("SELECT * FROM servers ORDER BY created_at DESC")
            return [dict(row) for row in cur.fetchall()]

    def delete(self, server_id: str) -> None:
        with self._db.cursor() as cur:
            cur.execute("DELETE FROM servers WHERE id = ?", (server_id,))


class TaskRepository:
    def __init__(self, db: Database | None = None) -> None:
        self._db = db or get_db()

    def create(self, name: str, priority: int) -> int:
        with self._db.cursor() as cur:
            cur.execute(
                "INSERT INTO tasks (name, priority, status) VALUES (?, ?, 'PENDING')",
                (name, priority),
            )
            return cur.lastrowid

    def update_status(self, task_id: int, status: str) -> None:
        with self._db.cursor() as cur:
            cur.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))

    def list_all(self) -> list[dict[str, Any]]:
        with self._db.cursor() as cur:
            cur.execute("SELECT * FROM tasks ORDER BY priority ASC, created_at ASC")
            return [dict(row) for row in cur.fetchall()]


class DeploymentRepository:
    def __init__(self, db: Database | None = None) -> None:
        self._db = db or get_db()

    def save_plan(self, plan_id: str, services: dict[str, list[str]]) -> None:
        """Persist a deployment plan: services + their dependency edges."""
        with self._db.cursor() as cur:
            for service_name, depends_on in services.items():
                cur.execute(
                    """
                    INSERT INTO deployments (id, plan_id, service_name, status)
                    VALUES (?, ?, ?, 'PENDING')
                    ON CONFLICT(plan_id, service_name) DO NOTHING
                    """,
                    (f"{plan_id}:{service_name}", plan_id, service_name),
                )
                for dep in depends_on:
                    cur.execute(
                        """
                        INSERT OR IGNORE INTO deployment_dependencies
                            (plan_id, service_name, depends_on_service)
                        VALUES (?, ?, ?)
                        """,
                        (plan_id, service_name, dep),
                    )

    def update_service_status(self, plan_id: str, service_name: str, status: str) -> None:
        with self._db.cursor() as cur:
            cur.execute(
                "UPDATE deployments SET status = ? WHERE plan_id = ? AND service_name = ?",
                (status, plan_id, service_name),
            )

    def get_plan(self, plan_id: str) -> list[dict[str, Any]]:
        with self._db.cursor() as cur:
            cur.execute("SELECT * FROM deployments WHERE plan_id = ?", (plan_id,))
            return [dict(row) for row in cur.fetchall()]

    def get_dependencies(self, plan_id: str) -> list[dict[str, Any]]:
        with self._db.cursor() as cur:
            cur.execute(
                "SELECT * FROM deployment_dependencies WHERE plan_id = ?", (plan_id,)
            )
            return [dict(row) for row in cur.fetchall()]


class LogRepository:
    def __init__(self, db: Database | None = None) -> None:
        self._db = db or get_db()

    def add(self, resource_id: str, level: str, message: str) -> None:
        with self._db.cursor() as cur:
            cur.execute(
                "INSERT INTO logs (resource_id, level, message) VALUES (?, ?, ?)",
                (resource_id, level, message),
            )

    def list_for_resource_sorted(self, resource_id: str) -> list[dict[str, Any]]:
        """Returns logs for a resource sorted by timestamp ascending.

        Sorted output is required by log_service's binary search.
        """
        with self._db.cursor() as cur:
            cur.execute(
                "SELECT * FROM logs WHERE resource_id = ? ORDER BY timestamp ASC",
                (resource_id,),
            )
            return [dict(row) for row in cur.fetchall()]