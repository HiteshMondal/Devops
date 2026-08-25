from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, status as http_status

from src.database import get_connection
from src.models import Stats, Task, TaskCreate, TaskUpdate

_UPDATABLE_FIELDS = ("title", "description", "status", "priority")


class TaskService:
    """Encapsulates all reads/writes against the tasks table."""

    def list_tasks(self) -> list[Task]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM tasks ORDER BY status, priority DESC, id DESC"
            ).fetchall()
        return [Task(**dict(row)) for row in rows]

    def get_task(self, task_id: int) -> Task:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
        if row is None:
            raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Task not found")
        return Task(**dict(row))

    def create_task(self, payload: TaskCreate) -> Task:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO tasks (title, description, priority)
                VALUES (?, ?, ?)
                """,
                (payload.title, payload.description, payload.priority.value),
            )
            conn.commit()
            task_id = cur.lastrowid
        return self.get_task(task_id)

    def update_task(self, task_id: int, payload: TaskUpdate) -> Task:
        updates = {
            field: getattr(payload, field)
            for field in _UPDATABLE_FIELDS
            if getattr(payload, field) is not None
        }
        if not updates:
            return self.get_task(task_id)

        set_clause = ", ".join(f"{field} = ?" for field in updates)
        values = [
            v.value if hasattr(v, "value") else v for v in updates.values()
        ]
        values.append(task_id)

        with get_connection() as conn:
            cur = conn.execute(
                f"""
                UPDATE tasks
                SET {set_clause}, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                WHERE id = ?
                """,
                values,
            )
            conn.commit()
            if cur.rowcount == 0:
                raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Task not found")
        return self.get_task(task_id)

    def delete_task(self, task_id: int) -> None:
        with get_connection() as conn:
            cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            if cur.rowcount == 0:
                raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Task not found")

    def stats(self) -> Stats:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) AS n FROM tasks GROUP BY status"
            ).fetchall()
        counts = {row["status"]: row["n"] for row in rows}
        backlog = counts.get("backlog", 0)
        in_progress = counts.get("in_progress", 0)
        done = counts.get("done", 0)
        return Stats(
            backlog=backlog,
            in_progress=in_progress,
            done=done,
            total=backlog + in_progress + done,
        )


task_service = TaskService()