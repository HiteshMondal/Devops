"""FastAPI dependency providers.

Centralizes construction of shared, process-wide service instances so
routes just declare a dependency instead of instantiating services
themselves.
"""

from __future__ import annotations

from functools import lru_cache

from src.core.config import get_settings
from src.core.patterns.rate_limiter import RateLimiter
from src.services.health_service import HealthService
from src.services.monitoring_service import MonitoringService
from src.services.scheduler_service import TaskScheduler


@lru_cache
def get_scheduler() -> TaskScheduler:
    return TaskScheduler()


@lru_cache
def get_monitoring_service() -> MonitoringService:
    settings = get_settings()
    return MonitoringService(capacity=settings.lru_cache_size)


@lru_cache
def get_health_service() -> HealthService:
    settings = get_settings()
    return HealthService(
        failure_threshold=settings.circuit_breaker_failure_threshold,
        reset_seconds=settings.circuit_breaker_reset_seconds,
    )


@lru_cache
def get_rate_limiter() -> RateLimiter:
    settings = get_settings()
    return RateLimiter(requests_per_minute=settings.rate_limit_per_minute)