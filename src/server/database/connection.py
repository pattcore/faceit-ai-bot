"""Database connection and session management"""

import os
import time
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from prometheus_client import Histogram
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

# Load environment variables from .env - use absolute path
project_root = Path(__file__).resolve().parent.parent.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=str(env_path))

# Use DATABASE_URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', '')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'faceit_bot')}",
)

engine: Engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


DB_QUERY_DURATION_SECONDS = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)


def _classify_sql_operation(statement: str) -> str:
    """Classify SQL statement into a low-cardinality operation label.

    Avoid using raw SQL text as a label to prevent cardinality explosion.
    """

    sql = (statement or "").lstrip().upper()
    if sql.startswith("SELECT"):
        return "select"
    if sql.startswith("INSERT"):
        return "insert"
    if sql.startswith("UPDATE"):
        return "update"
    if sql.startswith("DELETE"):
        return "delete"
    return "other"


@event.listens_for(engine, "before_cursor_execute")
def _before_cursor_execute(
    conn,
    cursor,
    statement,
    parameters,
    context,
    executemany,
):  # pragma: no cover - thin instrumentation wrapper
    conn.info.setdefault("query_start_time", []).append(time.perf_counter())


@event.listens_for(engine, "after_cursor_execute")
def _after_cursor_execute(
    conn,
    cursor,
    statement,
    parameters,
    context,
    executemany,
):  # pragma: no cover - thin instrumentation wrapper
    start_times = conn.info.get("query_start_time") or []
    if not start_times:
        return

    start_time = start_times.pop(-1)
    duration = time.perf_counter() - start_time

    try:
        op = _classify_sql_operation(statement)
        DB_QUERY_DURATION_SECONDS.labels(operation=op).observe(duration)
    except Exception:
        # Metrics must never break query execution
        pass


def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
