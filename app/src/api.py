from __future__ import annotations

from fastapi import APIRouter, status

from src.models import Stats, Task, TaskCreate, TaskUpdate
from src.services import task_service

router = APIRouter(prefix="/api/v1", tags=["tasks"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/tasks", response_model=list[Task])
def list_tasks() -> list[Task]:
    return task_service.list_tasks()


@router.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate) -> Task:
    return task_service.create_task(payload)


@router.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int) -> Task:
    return task_service.get_task(task_id)


@router.patch("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, payload: TaskUpdate) -> Task:
    return task_service.update_task(task_id, payload)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_task(task_id: int):
    task_service.delete_task(task_id)


@router.get("/stats", response_model=Stats)
def stats() -> Stats:
    return task_service.stats()