"""API routes for the DevOps console."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from src.api.dependencies import (
    get_health_service,
    get_monitoring_service,
    get_rate_limiter,
    get_scheduler,
)
from src.api.schemas import (
    DeploymentOrderOut,
    DeploymentPlanCreate,
    ServerCreate,
    ServerOut,
    TaskCreate,
    TaskOut,
)
from src.core.exceptions import CyclicDependencyError
from src.db.repository import DeploymentRepository, LogRepository, ServerRepository
from src.models.resource import Server
from src.models.task import Task
from src.services.deployment_service import build_plan, topological_deploy_order
from src.services.log_service import LogIndex

router = APIRouter()


def enforce_rate_limit(request: Request, limiter=Depends(get_rate_limiter)) -> None:
    client_key = request.client.host if request.client else "anonymous"
    if not limiter.allow(client_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


@router.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Servers
# ---------------------------------------------------------------------------


@router.post("/servers", response_model=ServerOut, tags=["servers"])
def create_server(
    payload: ServerCreate,
    health_service=Depends(get_health_service),
    monitoring=Depends(get_monitoring_service),
    _: None = Depends(enforce_rate_limit),
) -> ServerOut:
    server = Server(
        resource_id=payload.resource_id,
        name=payload.name,
        cpu_cores=payload.cpu_cores,
        memory_gb=payload.memory_gb,
        region=payload.region,
    )
    status = health_service.check(server)
    monitoring.record_status(server.resource_id, status.value)

    repo = ServerRepository()
    repo.upsert(
        server_id=server.resource_id,
        name=server.name,
        cpu_cores=server.cpu_cores,
        memory_gb=server.memory_gb,
        region=server.region,
        status=status.value,
    )
    return ServerOut(
        id=server.resource_id,
        name=server.name,
        cpu_cores=server.cpu_cores,
        memory_gb=server.memory_gb,
        region=server.region,
        status=status.value,
    )


@router.get("/servers", response_model=list[ServerOut], tags=["servers"])
def list_servers() -> list[ServerOut]:
    repo = ServerRepository()
    rows = repo.list_all()
    return [
        ServerOut(
            id=r["id"],
            name=r["name"],
            cpu_cores=r["cpu_cores"],
            memory_gb=r["memory_gb"],
            region=r["region"],
            status=r["status"],
        )
        for r in rows
    ]


@router.get("/servers/{server_id}/status", tags=["servers"])
def cached_server_status(server_id: str, monitoring=Depends(get_monitoring_service)) -> dict[str, str | None]:
    """Returns the LRU-cached status for a server, without hitting the DB."""
    return {"resource_id": server_id, "cached_status": monitoring.get_cached_status(server_id)}


# ---------------------------------------------------------------------------
# Tasks (priority-queue scheduler)
# ---------------------------------------------------------------------------


@router.post("/tasks", response_model=TaskOut, tags=["tasks"])
def submit_task(payload: TaskCreate, scheduler=Depends(get_scheduler)) -> TaskOut:
    task = Task(name=payload.name, priority=payload.priority)
    scheduler.submit(task)
    return TaskOut(task_id=task.task_id, name=task.name, priority=task.priority, status=task.status.value)


@router.get("/tasks/next", response_model=TaskOut | None, tags=["tasks"])
def pop_next_task(scheduler=Depends(get_scheduler)) -> TaskOut | None:
    task = scheduler.pop_next()
    if task is None:
        return None
    return TaskOut(task_id=task.task_id, name=task.name, priority=task.priority, status=task.status.value)


@router.get("/tasks", response_model=list[TaskOut], tags=["tasks"])
def list_pending_tasks(scheduler=Depends(get_scheduler)) -> list[TaskOut]:
    return [
        TaskOut(task_id=t.task_id, name=t.name, priority=t.priority, status=t.status.value)
        for t in scheduler.all_pending()
    ]


# ---------------------------------------------------------------------------
# Deployments (graph / topological sort)
# ---------------------------------------------------------------------------


@router.post("/deployments/plan", response_model=DeploymentOrderOut, tags=["deployments"])
def create_deployment_plan(payload: DeploymentPlanCreate) -> DeploymentOrderOut:
    plan = build_plan(payload.plan_id, payload.services)
    try:
        order = topological_deploy_order(plan)
    except CyclicDependencyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    repo = DeploymentRepository()
    repo.save_plan(payload.plan_id, payload.services)

    return DeploymentOrderOut(plan_id=payload.plan_id, order=order)


@router.get("/deployments/{plan_id}", tags=["deployments"])
def get_deployment_plan(plan_id: str) -> dict[str, list[dict]]:
    repo = DeploymentRepository()
    return {
        "services": repo.get_plan(plan_id),
        "dependencies": repo.get_dependencies(plan_id),
    }


# ---------------------------------------------------------------------------
# Logs (binary search index)
# ---------------------------------------------------------------------------


@router.post("/logs/{resource_id}", tags=["logs"])
def add_log(resource_id: str, level: str, message: str) -> dict[str, str]:
    repo = LogRepository()
    repo.add(resource_id, level, message)
    return {"status": "recorded"}


@router.get("/logs/{resource_id}/since/{timestamp}", tags=["logs"])
def logs_since(resource_id: str, timestamp: str) -> dict[str, list[dict]]:
    repo = LogRepository()
    sorted_logs = repo.list_for_resource_sorted(resource_id)
    index = LogIndex(sorted_logs)
    return {"logs": index.find_from(timestamp)}