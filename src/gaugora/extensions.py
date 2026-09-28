"""Shared extensions: SQLAlchemy engine/session and APScheduler."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()

engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None
scheduler = BackgroundScheduler()


def init_db(database_url: str) -> None:
    global engine, SessionLocal
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    engine = create_engine(database_url, connect_args=connect_args)

    if database_url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # noqa: ARG001
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    if SessionLocal is None:
        raise RuntimeError("Database not initialized")
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
