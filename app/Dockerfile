FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application source
COPY src ./src

# APP_PORT is the single source of truth (see .env). Default kept in sync
# with .env's APP_PORT=8000 so a plain `docker run` still works.
ENV APP_PORT=8000
EXPOSE 8000

# Shell form so ${APP_PORT} is resolved from the container's real
# environment at runtime (injected via the Kubernetes ConfigMap/Secret,
# docker-compose, or `docker run -e APP_PORT=...`).
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${APP_PORT:-8000} --log-level ${LOG_LEVEL:-info}"]