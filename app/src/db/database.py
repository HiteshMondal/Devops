"""
SQLite connection management.

Provides a single shared connection factory so the whole app talks to
the same database file, and applies schema.sql on startup.
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from src.core.config import get_settings

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


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
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._apply_schema()

    def _apply_schema(self) -> None:
        with open(_SCHEMA_PATH, "r", encoding="utf-8") as f:
            self._conn.executescript(f.read())
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
        """Close and reset the singleton. Mainly useful for tests."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance._conn.close()
            cls._instance = None


def get_db() -> Database:
    return Database()