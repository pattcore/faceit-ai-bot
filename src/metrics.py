"""
Prometheus metrics for monitoring
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import APIRouter, Response

router = APIRouter()

# Metrics
REQUEST_COUNT = Counter(
    'app_requests_total',
    'Total request count',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'app_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_USERS = Gauge(
    'app_active_users',
    'Number of active users'
)

PLAYER_ANALYSIS_COUNT = Counter(
    'app_player_analysis_total',
    'Total player analysis count'
)

TEAMMATE_SEARCHES = Counter(
    'app_teammate_searches_total',
    'Total teammate searches'
)


@router.get("/metrics")
async def metrics():
    """Endpoint for Prometheus scraping"""
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
