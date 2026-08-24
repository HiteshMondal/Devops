from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from typing import Any, Iterator

from src.config import get_settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS servers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    cpu_cores INTEGER NOT NULL DEFAULT 1,
    memory_gb INTEGER NOT NULL DEFAULT 1,
    region TEXT NOT NULL DEFAULT 'local',
    status TEXT NOT NULL DEFAULT 'UNKNOWN',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS deployments (
    id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    service_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    started_at TEXT,
    finished_at TEXT,
    UNIQUE (plan_id, service_name)
);

CREATE TABLE IF NOT EXISTS deployment_dependencies (
    plan_id TEXT NOT NULL,
    service_name TEXT NOT NULL,
    depends_on_service TEXT NOT NULL,
    PRIMARY KEY (plan_id, service_name, depends_on_service)
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 5,
    status TEXT NOT NULL DEFAULT 'PENDING',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_id TEXT NOT NULL,
    level TEXT NOT NULL DEFAULT 'INFO',
    message TEXT NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_logs_resource_ts
ON logs (resource_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_deployments_plan
ON deployments (plan_id);
"""


class Database:
    _instance: "Database | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "Database":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._init_db()
                    cls._instance = instance

        return cls._instance

    def _init_db(self) -> None:
        settings = get_settings()

        self._db_path = settings.db_path

        self._conn = sqlite3.connect(
            self._db_path,
            check_same_thread=False,
        )

        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")

        self._apply_schema()

    def _apply_schema(self) -> None:
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    @property
    def connection(self) -> sqlite3.Connection:
        return self._conn

    @contextmanager
    def cursor(self) -> Iterator[sqlite3.Cursor]:
        cur = self._conn.cursor()

        try:
            yield cur
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        finally:
            cur.close()

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            if cls._instance is not None:
                cls._instance._conn.close()

            cls._instance = None


def get_db() -> Database:
    return Database()


class ServerRepository:
    def __init__(self, db: Database | None = None) -> None:
        self._db = db or get_db()

    def upsert(
        self,
        server_id: str,
        name: str,
        cpu_cores: int,
        memory_gb: int,
        region: str,
        status: str,
    ) -> None:
        with self._db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO servers
                    (id, name, cpu_cores, memory_gb, region, status)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    cpu_cores=excluded.cpu_cores,
                    memory_gb=excluded.memory_gb,
                    region=excluded.region,
                    status=excluded.status
                """,
                (
                    server_id,
                    name,
                    cpu_cores,
                    memory_gb,
                    region,
                    status,
                ),
            )

    def get(self, server_id: str) -> dict[str, Any] | None:
        with self._db.cursor() as cur:
            cur.execute(
                "SELECT * FROM servers WHERE id = ?",
                (server_id,),
            )
            row = cur.fetchone()

            return dict(row) if row else None

    def list_all(self) -> list[dict[str, Any]]:
        with self._db.cursor() as cur:
            cur.execute(
                "SELECT * FROM servers ORDER BY created_at DESC"
            )
            return [dict(row) for row in cur.fetchall()]

    def delete(self, server_id: str) -> None:
        with self._db.cursor() as cur:
            cur.execute(
                "DELETE FROM servers WHERE id = ?",
                (server_id,),
            )


class TaskRepository:
    def __init__(self, db: Database | None = None) -> None:
        self._db = db or get_db()

    def create(self, name: str, priority: int) -> int:
        with self._db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tasks (name, priority, status)
                VALUES (?, ?, 'PENDING')
                """,
                (name, priority),
            )
            return cur.lastrowid

    def update_status(self, task_id: int, status: str) -> None:
        with self._db.cursor() as cur:
            cur.execute(
                "UPDATE tasks SET status = ? WHERE id = ?",
                (status, task_id),
            )

    def list_all(self) -> list[dict[str, Any]]:
        with self._db.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM tasks
                ORDER BY priority ASC, created_at ASC
                """
            )
            return [dict(row) for row in cur.fetchall()]


class DeploymentRepository:
    def __init__(self, db: Database | None = None) -> None:
        self._db = db or get_db()

    def save_plan(
        self,
        plan_id: str,
        services: dict[str, list[str]],
    ) -> None:
        with self._db.cursor() as cur:
            for service_name, depends_on in services.items():
                cur.execute(
                    """
                    INSERT INTO deployments
                        (id, plan_id, service_name, status)
                    VALUES (?, ?, ?, 'PENDING')
                    ON CONFLICT(plan_id, service_name)
                    DO NOTHING
                    """,
                    (
                        f"{plan_id}:{service_name}",
                        plan_id,
                        service_name,
                    ),
                )

                for dep in depends_on:
                    cur.execute(
                        """
                        INSERT OR IGNORE INTO deployment_dependencies
                            (plan_id, service_name, depends_on_service)
                        VALUES (?, ?, ?)
                        """,
                        (
                            plan_id,
                            service_name,
                            dep,
                        ),
                    )

    def update_service_status(
        self,
        plan_id: str,
        service_name: str,
        status: str,
    ) -> None:
        with self._db.cursor() as cur:
            cur.execute(
                """
                UPDATE deployments
                SET status = ?
                WHERE plan_id = ?
                  AND service_name = ?
                """,
                (
                    status,
                    plan_id,
                    service_name,
                ),
            )

    def get_plan(self, plan_id: str) -> list[dict[str, Any]]:
        with self._db.cursor() as cur:
            cur.execute(
                "SELECT * FROM deployments WHERE plan_id = ?",
                (plan_id,),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_dependencies(self, plan_id: str) -> list[dict[str, Any]]:
        with self._db.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM deployment_dependencies
                WHERE plan_id = ?
                """,
                (plan_id,),
            )
            return [dict(row) for row in cur.fetchall()]


class LogRepository:
    def __init__(self, db: Database | None = None) -> None:
        self._db = db or get_db()

    def add(
        self,
        resource_id: str,
        level: str,
        message: str,
    ) -> None:
        with self._db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO logs
                    (resource_id, level, message)
                VALUES (?, ?, ?)
                """,
                (resource_id, level, message),
            )

    def list_for_resource_sorted(
        self,
        resource_id: str,
    ) -> list[dict[str, Any]]:
        with self._db.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM logs
                WHERE resource_id = ?
                ORDER BY timestamp ASC
                """,
                (resource_id,),
            )
            return [dict(row) for row in cur.fetchall()]