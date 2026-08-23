# DevOps Console (app)

A small FastAPI service used as a learning/reference project for core
Data Structures & Algorithms, Object-Oriented Programming, basic
System Design, and SQL — all applied to realistic DevOps scenarios
(server health, task scheduling, deployment ordering, log search).

## Concepts covered

| Area                | Concept                          | Where |
|----------------------|-----------------------------------|-------|
| DSA                 | Priority queue (heap)             | `src/services/scheduler_service.py` |
| DSA                 | Graph + topological sort          | `src/services/deployment_service.py` |
| DSA                 | LRU cache                         | `src/services/monitoring_service.py` |
| DSA                 | Binary search                     | `src/services/log_service.py` |
| OOP                 | Abstraction / inheritance / polymorphism | `src/models/resource.py` |
| OOP                 | Custom exception hierarchy        | `src/core/exceptions.py` |
| System Design       | Singleton (config, DB connection) | `src/core/config.py`, `src/db/database.py` |
| System Design       | Observer pattern (alerting)       | `src/core/patterns/observer.py` |
| System Design       | Circuit breaker                   | `src/core/patterns/circuit_breaker.py` |
| System Design       | Token-bucket rate limiter         | `src/core/patterns/rate_limiter.py` |
| System Design       | Repository pattern                | `src/db/repository.py` |
| SQL                 | Schema + queries (SQLite)         | `src/db/schema.sql`, `src/db/repository.py` |

## Project layout

```
app/
├── src/
│   ├── api/          # FastAPI routes, request/response schemas, DI wiring
│   ├── core/          # config, logging, exceptions, design patterns
│   │   └── patterns/  # observer, circuit breaker, rate limiter
│   ├── db/            # SQLite connection + schema.sql + repositories
│   ├── models/        # OOP domain models (Resource, Task, Deployment)
│   ├── services/       # business logic (scheduler, deployment, monitoring, logs, health)
│   └── main.py         # FastAPI app entrypoint
├── tests/               # pytest test suite
├── Dockerfile
├── .dockerignore
├── requirements.txt
└── README.md
```

## Running locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn src.main:app --reload --port 8000
```

Then open http://127.0.0.1:8000/docs for interactive API docs.

### Environment variables

| Variable                        | Default        | Purpose |
|----------------------------------|-----------------|---------|
| `APP_ENV`                        | `local`         | Environment name (local/production/etc.) |
| `DB_PATH`                        | `app.db`        | Path to the SQLite database file |
| `LOG_LEVEL`                      | `INFO`          | Root logger level |
| `MAX_CONCURRENT_DEPLOYMENTS`     | `3`             | Reserved for future deployment concurrency control |
| `RATE_LIMIT_PER_MINUTE`          | `60`            | API rate limit per client |
| `LRU_CACHE_SIZE`                 | `128`           | Max entries in the health-status LRU cache |
| `CB_FAILURE_THRESHOLD`           | `5`             | Failures before the circuit breaker opens |
| `CB_RESET_SECONDS`               | `30`            | Seconds before an open circuit tries to recover |

## Running tests

```bash
pip install -r requirements.txt
python3 -m pytest tests/ -v
```

## Running with Docker

```bash
docker build -t devops-console .
docker run --rm -p 8000:8000 -v devops_data:/data devops-console
```

## Key API endpoints

- `GET  /api/v1/health` — liveness check
- `POST /api/v1/servers` — register a server, runs a health check, persists to SQL
- `GET  /api/v1/servers` — list servers from SQL
- `GET  /api/v1/servers/{id}/status` — cached (LRU) status lookup
- `POST /api/v1/tasks` — enqueue a task onto the priority-queue scheduler
- `GET  /api/v1/tasks/next` — pop the highest-priority pending task
- `POST /api/v1/deployments/plan` — submit a service dependency graph, get back a valid deploy order (topological sort)
- `GET  /api/v1/deployments/{plan_id}` — read a persisted deployment plan from SQL
- `POST /api/v1/logs/{resource_id}` — append a log line
- `GET  /api/v1/logs/{resource_id}/since/{timestamp}` — binary-search log lookup by timestamp