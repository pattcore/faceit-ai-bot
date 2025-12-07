"""
Database configuration, SQLAlchemy setup, and DB pool metrics.
"""

import sys
from pathlib import Path
from typing import Any, Dict

from prometheus_client import Counter, Gauge
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import Pool, StaticPool

sys.path.append(str(Path(__file__).parent))
from config.settings import settings


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


def _instrument_engine(engine, pool_label: str = "primary") -> None:
    """Attach Prometheus instrumentation to the engine's pool."""

    pool: Pool | None = getattr(engine, "pool", None)
    if pool is None:
        return

    # Avoid double-registration when tests reload this module
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

    def _safe_inc(metric_key: str) -> None:
        try:
            counters[metric_key].inc()
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
        # close fires when pool disposes a DBAPI connection
        state["total"] = max(state["total"] - 1, 0)
        _update_gauges()

    def _invalidate(dbapi_connection, connection_record, exception) -> None:
        _safe_inc("invalidate")

    event.listen(pool, "checkout", _checkout)
    event.listen(pool, "checkin", _checkin)
    event.listen(pool, "connect", _connect)
    event.listen(pool, "close", _close)
    event.listen(pool, "invalidate", _invalidate)


def _create_engine():
    """Create and instrument SQLAlchemy engine based on settings."""
    if settings.DATABASE_URL.startswith("sqlite"):
        engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

    try:
        _instrument_engine(engine, pool_label="primary")
    except Exception:
        # Metrics instrumentation must never block engine creation
        pass

    return engine


# Global engine and session factory
engine = _create_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency for getting database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
