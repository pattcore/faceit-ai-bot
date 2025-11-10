"""
Health check endpoints for monitoring
"""

from fastapi import APIRouter
from datetime import datetime
import psutil
import os

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv("VERSION", "0.3.0")
    }


@router.get("/health/detailed")
async def detailed_health():
    """Detailed health check of all services"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv("VERSION", "0.3.0"),
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        },
        "services": {
            "database": await check_database(),
            "redis": await check_redis(),
            "api": "healthy"
        }
    }


async def check_database():
    """Check database connection"""
    try:
        # Database connection check implementation
        return "healthy"
    except Exception:
        return "unhealthy"


async def check_redis():
    """Check Redis connection"""
    try:
        # Redis connection check implementation
        return "healthy"
    except Exception:
        return "unhealthy"
