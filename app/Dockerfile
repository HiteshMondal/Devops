FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application source
COPY src ./src

# Writable location for the SQLite database file (see DB_SQLITE_PATH in
# src/config.py). Created here so it exists even if no volume is mounted.
RUN mkdir -p /app/data

# APP_PORT is the single source of truth (see .env). Default kept in sync
# with .env's APP_PORT=8000 so a plain `docker run` still works.
ENV APP_PORT=8000
EXPOSE 8000

# Shell form so ${APP_PORT} is resolved from the container's real
# environment at runtime (injected via the Kubernetes ConfigMap/Secret,
# docker-compose, or `docker run -e APP_PORT=...`).
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${APP_PORT:-8000} --log-level ${LOG_LEVEL:-info}"]
