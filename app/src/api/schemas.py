"""Pydantic request/response models for the API layer."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ServerCreate(BaseModel):
    resource_id: str
    name: str
    cpu_cores: int = 1
    memory_gb: int = 1
    region: str = "local"


class ServerOut(BaseModel):
    id: str
    name: str
    cpu_cores: int
    memory_gb: int
    region: str
    status: str


class TaskCreate(BaseModel):
    name: str
    priority: int = Field(default=5, ge=0, le=10)


class TaskOut(BaseModel):
    task_id: int
    name: str
    priority: int
    status: str


class DeploymentPlanCreate(BaseModel):
    plan_id: str
    # service_name -> list of service names it depends on
    services: dict[str, list[str]]


class DeploymentOrderOut(BaseModel):
    plan_id: str
    order: list[str]