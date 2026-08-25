"""Centralized application settings, sourced entirely from environment
variables so the same image runs unmodified in any environment (local,
Docker Compose, Minikube, Kind, k3s, EKS, GKE, AKS, ...).
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    app_name: str = os.environ.get("APP_NAME", "devops-app")
    app_env: str = os.environ.get("APP_ENV", "production")
    log_level: str = os.environ.get("LOG_LEVEL", "info")
    app_port: int = _env_int("APP_PORT", 8000)
    db_path: str = os.environ.get("DB_PATH", "/data/app.db")


settings = Settings()