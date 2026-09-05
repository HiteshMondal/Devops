"""Environment-driven configuration.

Reads the exact variable names defined in `.env` and injected at runtime by
`platform/deployment/kubernetes/deploy_kubernetes.sh` (ConfigMap `devops-app-config`
and Secret `devops-app-secrets`). These names are a shared contract with the
rest of the platform — do not rename them here.
"""
import os


def _str(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


class Config:
    # Application
    APP_NAME = _str("APP_NAME", "devops-app")
    APP_ENV = _str("APP_ENV", "local")          # "local" | "production" — set by run.sh
    APP_PORT = _int("APP_PORT", 8000)
    LOG_LEVEL = _str("LOG_LEVEL", "info")

    # Database — same env-var contract as before. If DB_HOST points at a real
    # database, wire a driver of your choice into database.py later. Until
    # then, an on-disk SQLite file is used so the app runs with zero extra
    # infra locally and in any cluster.
    DB_HOST = _str("DB_HOST", "localhost")
    DB_PORT = _int("DB_PORT", 5432)
    DB_NAME = _str("DB_NAME", "devopsdb")
    DB_USERNAME = _str("DB_USERNAME", "devops")
    DB_PASSWORD = _str("DB_PASSWORD", "")
    DB_SQLITE_PATH = _str("DB_SQLITE_PATH", "/app/data/app.db")

    # Secrets — never exposed via the API, only read for internal use
    JWT_SECRET = _str("JWT_SECRET", "")
    API_KEY = _str("API_KEY", "")
    SESSION_SECRET = _str("SESSION_SECRET", "")


config = Config()
