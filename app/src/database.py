"""Lightweight SQLite access layer. No ORM dependency is required, which
keeps the container image small and the schema easy to inspect.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from src.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'backlog'
                CHECK (status IN ('backlog', 'in_progress', 'done')),
    priority    TEXT NOT NULL DEFAULT 'medium'
                CHECK (priority IN ('low', 'medium', 'high')),
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
"""


def _ensure_parent_dir(path: str) -> None:
    parent = Path(path).parent
    if str(parent) not in ("", "."):
        os.makedirs(parent, exist_ok=True)


def init_db() -> None:
    """Create the database file and schema if they don't exist yet."""
    _ensure_parent_dir(settings.db_path)
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        conn.commit()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(settings.db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
    finally:
        conn.close()