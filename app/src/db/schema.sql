-- Schema for the DevOps console application.
-- SQLite dialect; kept intentionally simple/portable.

CREATE TABLE IF NOT EXISTS servers (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    cpu_cores     INTEGER NOT NULL DEFAULT 1,
    memory_gb     INTEGER NOT NULL DEFAULT 1,
    region        TEXT NOT NULL DEFAULT 'local',
    status        TEXT NOT NULL DEFAULT 'UNKNOWN',
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS deployments (
    id            TEXT PRIMARY KEY,
    plan_id       TEXT NOT NULL,
    service_name  TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'PENDING',
    started_at    TEXT,
    finished_at   TEXT,
    UNIQUE (plan_id, service_name)
);

CREATE TABLE IF NOT EXISTS deployment_dependencies (
    plan_id           TEXT NOT NULL,
    service_name      TEXT NOT NULL,
    depends_on_service TEXT NOT NULL,
    PRIMARY KEY (plan_id, service_name, depends_on_service)
);

CREATE TABLE IF NOT EXISTS tasks (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    priority      INTEGER NOT NULL DEFAULT 5,
    status        TEXT NOT NULL DEFAULT 'PENDING',
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS logs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_id   TEXT NOT NULL,
    level         TEXT NOT NULL DEFAULT 'INFO',
    message       TEXT NOT NULL,
    timestamp     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_logs_resource_ts ON logs (resource_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_deployments_plan ON deployments (plan_id);