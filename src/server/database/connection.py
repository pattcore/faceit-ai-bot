"""Database connection and session management with metrics."""

import os
import time
from pathlib import Path
from typing import Dict, Generator

from dotenv import load_dotenv
from prometheus_client import Counter, Gauge, Histogram
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import Pool, StaticPool

# Load environment variables from .env - use absolute path
project_root = Path(__file__).resolve().parent.parent.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=str(env_path))

# Use DATABASE_URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', '')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'faceit_bot')}",
)


DB_QUERY_DURATION_SECONDS = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)


DB_POOL_CHECKOUTS_TOTAL = Counter(
    "db_pool_checkouts_total",
    "Total database pool checkouts",
    ["pool"],
)


DB_POOL_CHECKINS_TOTAL = Counter(
    "db_pool_checkins_total",
    "Total database pool checkins",
    ["pool"],
)


DB_POOL_NEW_CONNECTIONS_TOTAL = Counter(
    "db_pool_new_connections_total",
    "Total new DBAPI connections established by the pool",
    ["pool"],
)


DB_POOL_INVALIDATIONS_TOTAL = Counter(
    "db_pool_invalidations_total",
    "Total pool invalidations due to disconnects or errors",
    ["pool"],
)


DB_POOL_CONNECTIONS_IN_USE = Gauge(
    "db_pool_connections_in_use",
    "Current number of DB connections checked out from the pool",
    ["pool"],
)


DB_POOL_TOTAL_CONNECTIONS = Gauge(
    "db_pool_total_connections",
    "Total number of DB connections currently opened by the pool",
    ["pool"],
)


def _classify_sql_operation(statement: str) -> str:
    """Classify SQL statement into a low-cardinality operation label."""

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


def _instrument_pool(engine: Engine, pool_label: str = "primary") -> None:
    """Attach Prometheus instrumentation to the engine's pool."""

    pool: Pool | None = getattr(engine, "pool", None)
    if pool is None:
        return

    if getattr(pool, "_metrics_instrumented", False):
        return
    setattr(pool, "_metrics_instrumented", True)

    counters = {
        "checkout": DB_POOL_CHECKOUTS_TOTAL.labels(pool=pool_label),
        "checkin": DB_POOL_CHECKINS_TOTAL.labels(pool=pool_label),
        "connect": DB_POOL_NEW_CONNECTIONS_TOTAL.labels(pool=pool_label),
        "invalidate": DB_POOL_INVALIDATIONS_TOTAL.labels(pool=pool_label),
    }
    gauges = {
        "in_use": DB_POOL_CONNECTIONS_IN_USE.labels(pool=pool_label),
        "total": DB_POOL_TOTAL_CONNECTIONS.labels(pool=pool_label),
    }

    state: Dict[str, int] = {"in_use": 0, "total": 0}

    def _update_gauges() -> None:
        try:
            gauges["in_use"].set(max(state["in_use"], 0))
            gauges["total"].set(max(state["total"], 0))
        except Exception:
            pass

    def _safe_inc(key: str) -> None:
        try:
            counters[key].inc()
        except Exception:
            pass

    def _checkout(dbapi_connection, connection_record, connection_proxy) -> None:
        state["in_use"] += 1
        _safe_inc("checkout")
        _update_gauges()

    def _checkin(dbapi_connection, connection_record) -> None:
        state["in_use"] = max(state["in_use"] - 1, 0)
        _safe_inc("checkin")
        _update_gauges()

    def _connect(dbapi_connection, connection_record) -> None:
        state["total"] += 1
        _safe_inc("connect")
        _update_gauges()

    def _close(dbapi_connection, connection_record) -> None:
        state["total"] = max(state["total"] - 1, 0)
        _update_gauges()

    def _invalidate(dbapi_connection, connection_record, exception) -> None:
        _safe_inc("invalidate")

    event.listen(pool, "checkout", _checkout)
    event.listen(pool, "checkin", _checkin)
    event.listen(pool, "connect", _connect)
    event.listen(pool, "close", _close)
    event.listen(pool, "invalidate", _invalidate)


def _create_engine() -> Engine:
    """Create and instrument SQLAlchemy engine based on env settings."""
    if DATABASE_URL.startswith("sqlite"):
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    try:
        _instrument_pool(engine, pool_label="primary")
    except Exception:
        # Metrics must never block database initialization
        pass

    return engine


engine: Engine = _create_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
        pass


def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
