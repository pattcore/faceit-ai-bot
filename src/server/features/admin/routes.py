import logging
from typing import Any, Dict, List, Literal

from fastapi import APIRouter, Depends, HTTPException, Request

from ...auth.dependencies import get_current_admin_user
from ...services.cache_service import cache_service
from ...config.settings import settings
from ...core.structured_logging import business_logger

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/rate-limit",
    tags=["admin"],
    dependencies=[Depends(get_current_admin_user)],
)


@router.get("/config")
async def get_rate_limit_config() -> Dict[str, Any]:
    redis_enabled = getattr(cache_service, "enabled", False) and cache_service.redis_client is not None
    return {
        "redis_enabled": redis_enabled,
        "rate_limit": {
            "requests_per_minute": settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
            "requests_per_hour": settings.RATE_LIMIT_REQUESTS_PER_HOUR,
            "ban_enabled": settings.RATE_LIMIT_BAN_ENABLED,
            "ban_threshold": settings.RATE_LIMIT_BAN_THRESHOLD,
            "ban_window_seconds": settings.RATE_LIMIT_BAN_WINDOW_SECONDS,
            "ban_ttl_seconds": settings.RATE_LIMIT_BAN_TTL_SECONDS,
        },
    }


@router.get("/bans")
async def list_rate_limit_bans() -> Dict[str, Any]:
    """List active rate limit bans (IP and users) from Redis."""
    if not getattr(cache_service, "enabled", False) or cache_service.redis_client is None:
        return {"enabled": False, "bans": []}

    client = cache_service.redis_client
    bans: List[Dict[str, Any]] = []

    try:
        cursor: int = 0
        pattern = "rate:ban:*"

        while True:
            cursor, keys = await client.scan(cursor=cursor, match=pattern, count=100)
            for key in keys:
                ttl = await client.ttl(key)

                if key.startswith("rate:ban:ip:"):
                    ban_type = "ip"
                    value = key[len("rate:ban:ip:") :]
                elif key.startswith("rate:ban:user:"):
                    ban_type = "user"
                    value = key[len("rate:ban:user:") :]
                else:
                    continue

                bans.append({"type": ban_type, "value": value, "ttl": ttl})

            if cursor == 0:
                break
    except Exception as e:  # pragma: no cover - defensive logging
        logger.error("Failed to list rate limit bans: %s", e)
        raise HTTPException(status_code=500, detail="Failed to list rate limit bans")

    return {"enabled": True, "bans": bans}


@router.delete("/bans/{kind}/{value}")
async def delete_rate_limit_ban(
    kind: Literal["ip", "user"],
    value: str,
    request: Request,
) -> Dict[str, Any]:
    """Remove rate limit ban and violation counters for IP or user."""
    if not getattr(cache_service, "enabled", False) or cache_service.redis_client is None:
        raise HTTPException(
            status_code=400,
            detail="Rate limiting with Redis is not enabled",
        )

    client = cache_service.redis_client

    try:
        ban_key = f"rate:ban:{kind}:{value}"
        viol_key = f"rate:viol:{kind}:{value}"

        removed_ban = await client.delete(ban_key)
        removed_viol = await client.delete(viol_key)

        logger.info(
            "Rate limit ban cleared: kind=%s value=%s removed_ban=%s removed_viol=%s",
            kind,
            value,
            removed_ban,
            removed_viol,
        )

        admin_id = getattr(request.state, "user_id", None)
        try:
            business_logger.logger.info(
                "admin_rate_limit_ban_cleared",
                admin_id=admin_id,
                kind=kind,
                value=value,
                removed_ban=int(removed_ban),
                removed_violations=int(removed_viol),
            )
        except Exception:
            logger.exception("Failed to log admin rate limit ban clear event")

        return {
            "kind": kind,
            "value": value,
            "removed_ban": int(removed_ban),
            "removed_violations": int(removed_viol),
        }
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover - defensive logging
        logger.error("Failed to clear rate limit ban for %s=%s: %s", kind, value, e)
        raise HTTPException(status_code=500, detail="Failed to clear rate limit ban")


@router.get("/violations")
async def list_rate_limit_violations() -> Dict[str, Any]:
    if not getattr(cache_service, "enabled", False) or cache_service.redis_client is None:
        return {"enabled": False, "violations": []}

    client = cache_service.redis_client
    violations: List[Dict[str, Any]] = []

    try:
        cursor: int = 0
        pattern = "rate:viol:*"

        while True:
            cursor, keys = await client.scan(cursor=cursor, match=pattern, count=100)
            for key in keys:
                ttl = await client.ttl(key)
                count = await client.get(key)

                if key.startswith("rate:viol:ip:"):
                    viol_type = "ip"
                    value = key[len("rate:viol:ip:") :]
                elif key.startswith("rate:viol:user:"):
                    viol_type = "user"
                    value = key[len("rate:viol:user:") :]
                else:
                    continue

                violations.append(
                    {
                        "type": viol_type,
                        "value": value,
                        "count": int(count) if count is not None else 0,
                        "ttl": ttl,
                    }
                )

            if cursor == 0:
                break
    except Exception as e:  # pragma: no cover - defensive logging
        logger.error("Failed to list rate limit violations: %s", e)
        raise HTTPException(status_code=500, detail="Failed to list rate limit violations")

    return {"enabled": True, "violations": violations}


@router.post("/violations/cleanup")
async def cleanup_rate_limit_violations(request: Request) -> Dict[str, Any]:
    if not getattr(cache_service, "enabled", False) or cache_service.redis_client is None:
        raise HTTPException(
            status_code=400,
            detail="Rate limiting with Redis is not enabled",
        )

    client = cache_service.redis_client

    try:
        cursor: int = 0
        pattern = "rate:viol:*"
        removed_total = 0

        while True:
            cursor, keys = await client.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                removed = await client.delete(*keys)
                removed_total += int(removed)
            if cursor == 0:
                break

        logger.info("Rate limit violations cleanup: removed=%s", removed_total)

        admin_id = getattr(request.state, "user_id", None)
        try:
            business_logger.logger.info(
                "admin_rate_limit_violations_cleanup",
                admin_id=admin_id,
                removed=removed_total,
            )
        except Exception:
            logger.exception("Failed to log admin rate limit violations cleanup event")

        return {"removed": removed_total}
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover - defensive logging
        logger.error("Failed to cleanup rate limit violations: %s", e)
        raise HTTPException(status_code=500, detail="Failed to cleanup rate limit violations")


@router.post("/bans/{kind}/{value}")
async def create_rate_limit_ban(
    kind: Literal["ip", "user"],
    value: str,
    request: Request,
) -> Dict[str, Any]:
    if not getattr(cache_service, "enabled", False) or cache_service.redis_client is None:
        raise HTTPException(
            status_code=400,
            detail="Rate limiting with Redis is not enabled",
        )

    client = cache_service.redis_client

    try:
        ban_key = f"rate:ban:{kind}:{value}"
        ttl = settings.RATE_LIMIT_BAN_TTL_SECONDS

        await client.setex(ban_key, ttl, "1")

        logger.info(
            "Rate limit ban created: kind=%s value=%s ttl=%s",
            kind,
            value,
            ttl,
        )

        admin_id = getattr(request.state, "user_id", None)
        try:
            business_logger.logger.info(
                "admin_rate_limit_ban_created",
                admin_id=admin_id,
                kind=kind,
                value=value,
                ttl=ttl,
            )
        except Exception:
            logger.exception("Failed to log admin rate limit ban create event")

        return {
            "kind": kind,
            "value": value,
            "ttl": ttl,
        }
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover - defensive logging
        logger.error("Failed to create rate limit ban for %s=%s: %s", kind, value, e)
        raise HTTPException(status_code=500, detail="Failed to create rate limit ban")
