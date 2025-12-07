import importlib

from prometheus_client import REGISTRY
from sqlalchemy import text

import src.server.database.connection as connection_module

METRIC_ATTRS = [
    "DB_QUERY_DURATION_SECONDS",
    "DB_POOL_CHECKOUTS_TOTAL",
    "DB_POOL_CHECKINS_TOTAL",
    "DB_POOL_NEW_CONNECTIONS_TOTAL",
    "DB_POOL_INVALIDATIONS_TOTAL",
    "DB_POOL_CONNECTIONS_IN_USE",
    "DB_POOL_TOTAL_CONNECTIONS",
]


def _unregister_metrics(module):
    for attr in METRIC_ATTRS:
        metric = getattr(module, attr, None)
        if metric is None:
            continue
        try:
            REGISTRY.unregister(metric)
        except KeyError:
            pass


def _reload_connection(monkeypatch):
    """Reload database.connection with sqlite URL to keep tests isolated."""
    _unregister_metrics(connection_module)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    return importlib.reload(connection_module)


def _get_metric_value(metric, attr: str = "_value"):
    """Best-effort helper to read Prometheus metric internals."""
    try:
        return getattr(metric, attr).get()  # type: ignore[attr-defined]
    except Exception:
        return None


def test_db_pool_metrics_increment_for_session_checkout(monkeypatch):
    db = _reload_connection(monkeypatch)

    session = db.SessionLocal()
    try:
        session.execute(text("SELECT 1"))
    finally:
        session.close()

    checkout = db.DB_POOL_CHECKOUTS_TOTAL.labels(pool="primary")
    checkin = db.DB_POOL_CHECKINS_TOTAL.labels(pool="primary")
    new_conn = db.DB_POOL_NEW_CONNECTIONS_TOTAL.labels(pool="primary")
    in_use = db.DB_POOL_CONNECTIONS_IN_USE.labels(pool="primary")

    assert (_get_metric_value(checkout) or 0) >= 1
    assert (_get_metric_value(checkin) or 0) >= 1
    assert (_get_metric_value(new_conn) or 0) >= 1
    # Connections in use should return to zero after checkin
    assert (_get_metric_value(in_use) or 0) == 0
