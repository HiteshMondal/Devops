"""
Application configuration.

System Design concept: Singleton pattern.
Only one Settings instance should ever exist for the lifetime of the
process so every module reads the same configuration values.
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field


@dataclass
class _SettingsData:
    app_name: str = "devops-console"
    env: str = field(default_factory=lambda: os.getenv("APP_ENV", "local"))
    db_path: str = field(default_factory=lambda: os.getenv("DB_PATH", "app.db"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    max_concurrent_deployments: int = field(
        default_factory=lambda: int(os.getenv("MAX_CONCURRENT_DEPLOYMENTS", "3"))
    )
    rate_limit_per_minute: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    )
    lru_cache_size: int = field(
        default_factory=lambda: int(os.getenv("LRU_CACHE_SIZE", "128"))
    )
    circuit_breaker_failure_threshold: int = field(
        default_factory=lambda: int(os.getenv("CB_FAILURE_THRESHOLD", "5"))
    )
    circuit_breaker_reset_seconds: int = field(
        default_factory=lambda: int(os.getenv("CB_RESET_SECONDS", "30"))
    )


class Settings:
    """Thread-safe Singleton wrapper around _SettingsData."""

    _instance: "Settings | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "Settings":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # double-checked locking
                    instance = super().__new__(cls)
                    instance._data = _SettingsData()
                    cls._instance = instance
        return cls._instance

    def __getattr__(self, item):
        return getattr(self._data, item)

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton. Mainly useful for tests."""
        with cls._lock:
            cls._instance = None


def get_settings() -> Settings:
    """Dependency-injectable accessor for the Settings singleton."""
    return Settings()