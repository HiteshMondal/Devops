"""Database engine & session setup.

Uses SQLite by default (zero extra infra, fine for a portfolio site's read-
heavy / low-write-volume workload). The existing DB_* env vars from `.env`
are honored and unused for now — if you later move to Postgres/MySQL, swap
SQLALCHEMY_URL below to build a proper DSN from those variables and add the
driver to requirements.txt. No other code needs to change.
"""
import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import config

os.makedirs(os.path.dirname(config.DB_SQLITE_PATH), exist_ok=True)

SQLALCHEMY_URL = f"sqlite:///{config.DB_SQLITE_PATH}"

engine = create_engine(SQLALCHEMY_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    from . import models  # noqa: F401 — ensure models are registered
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session():
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
