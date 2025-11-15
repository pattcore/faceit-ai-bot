"""Main FastAPI application entry point."""

import logging
from fastapi import FastAPI, Request, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, Counter, Histogram

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
from .features.tasks.routes import router as tasks_router

# Configure logging
setup_logging()

# Configure Sentry
init_sentry()

# Configure telemetry
init_telemetry()

# Business metrics
ANALYSIS_REQUESTS = Counter(
    "faceit_analysis_requests_total", "Total analysis requests"
)
ANALYSIS_DURATION = Histogram(
    "faceit_analysis_duration_seconds", "Analysis duration"
)
ACTIVE_USERS = Counter(
    "faceit_active_users", "Active user sessions"
)

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    debug=False,
    docs_url="/docs",
    redoc_url="/redoc",
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
        "name": "MIT",
    },
)

# Add structured logging middleware
app.add_middleware(StructuredLoggingMiddleware)

# Add security middleware
app.add_middleware(SecurityMiddleware)

# Add caching middleware
app.add_middleware(CacheMiddleware, cache_ttl=300)  # 5 minutes cache

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
app.include_router(tasks_router)


@app.get("/", tags=["health"])
def root():
    return {"message": "Faceit AI Bot service running", "status": "healthy"}


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy", "service": "backend"}


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain; charset=utf-8")
