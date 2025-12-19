"""Main FastAPI application entry point."""

import logging
import os
import sys
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, Counter

from .config.settings import settings
from .core.logging import setup_logging
from .core.sentry import init_sentry, capture_exception
from .core.telemetry import init_telemetry
from .middleware.logging_middleware import StructuredLoggingMiddleware
from .middleware.security_middleware import SecurityMiddleware
from .middleware.cache_middleware import CacheMiddleware
from .auth.routes import router as auth_router
from .features.ai_analysis.routes import router as ai_router
from .features.payments.routes import router as payment_router
from .features.subscriptions.routes import router as subscriptions_router
from .features.teammates.routes import router as teammates_router
from .features.player_analysis.routes import router as player_router
from .features.player_analysis.service import PlayerAnalysisService
from .features.player_analysis.schemas import PlayerAnalysisResponse
from .features.tasks.routes import router as tasks_router
from .features.admin.routes import router as admin_router
from .features.demo_analyzer.routes import router as demo_router
from .metrics_business import ANALYSIS_REQUESTS, ANALYSIS_DURATION, ACTIVE_USERS
from .sitemap_routes import router as sitemap_router

# Configure logging
setup_logging()

# Configure Sentry
init_sentry()

# Configure telemetry
init_telemetry()

# Business metrics are defined in metrics_business and imported above


def validate_env() -> None:
    """Validate presence of critical environment variables.

    This is a simple fail-fast check so that misconfigured deployments do
    not start silently with missing secrets or database URL.
    """

    required_vars = [
        "DATABASE_URL",
        "SECRET_KEY",
        "TURNSTILE_SECRET_KEY",
    ]

    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"ERROR: Missing required environment variables: {missing}", file=sys.stderr)
        # Non-zero exit so container / process manager can restart with proper config
        sys.exit(1)


validate_env()


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    debug=False,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    description="""
    Faceit AI Bot API - Аналитическая платформа для игроков Faceit

    ## Возможности

    * **Анализ игроков** - детальная статистика и рекомендации
    * **AI анализ** - машинное обучение для предсказаний
    * **Управление подписками** - премиум возможности
    * **Командная аналитика** - статистика тиммейтов

    ## Аутентификация

    Используйте JWT токены для доступа к защищенным эндпоинтам:
    ```
    Authorization: Bearer <your_jwt_token>
    ```

    ## Rate Limiting

    API имеет ограничения:
    - 60 запросов в минуту
    - 1000 запросов в час
    """,
    contact={
        "name": "Faceit AI Bot Support",
        "email": "support@faceit-ai-bot.com",
    },
    license_info={
        "name": "Source-available (see LICENSE)",
    },
)

# Add structured logging middleware
app.add_middleware(StructuredLoggingMiddleware)

# Add security middleware
app.add_middleware(SecurityMiddleware)

# Caching middleware temporarily disabled due to Content-Length issues
# app.add_middleware(CacheMiddleware, cache_ttl=300)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Exception handlers


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger = logging.getLogger(__name__)
    logger.exception(f"Unhandled exception: {str(exc)}")
    capture_exception(exc, {"path": str(request.url.path)})
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "path": request.url.path,
        },
    )


# Include routers (nginx adds /api prefix)
app.include_router(auth_router)
app.include_router(payment_router)
app.include_router(subscriptions_router)
app.include_router(teammates_router)
app.include_router(player_router)
app.include_router(ai_router)
app.include_router(demo_router)
app.include_router(tasks_router)
app.include_router(admin_router)
app.include_router(sitemap_router)


@app.get("/players/{nickname}/analysis", response_model=PlayerAnalysisResponse, tags=["players"])
async def analyze_player_route(nickname: str):
    service = PlayerAnalysisService()
    try:
        ANALYSIS_REQUESTS.inc()
        with ANALYSIS_DURATION.time():
            analysis = await service.analyze_player(nickname)
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"Player '{nickname}' not found",
            )
        return analysis
    except HTTPException:
        raise
    except Exception as exc:
        logger = logging.getLogger(__name__)
        logger.error(f"Error analyzing player {nickname}: {exc}")
        raise HTTPException(status_code=500, detail="Failed to analyze player")


@app.get("/", tags=["health"])
def root():
    return {"message": "Faceit AI Bot service running", "status": "healthy"}


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy", "service": "backend"}


@app.get("/api/health", tags=["health"])
def health_check_api():
    """Alias endpoint for /health when proxied through /api prefix."""
    return {"status": "healthy", "service": "backend", "path": "/api/health"}


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain; charset=utf-8")
