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
from .features.auth.routes import router as auth_router
from .features.ai_analysis.routes import router as ai_router
from .features.payment.routes import router as payment_router
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

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    debug=False,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add structured logging middleware
app.add_middleware(StructuredLoggingMiddleware)

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
            "path": request.url.path
        }
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)


# Business metrics
ANALYSIS_REQUESTS = Counter(
    'faceit_analysis_requests_total', 'Total analysis requests'
)
ANALYSIS_DURATION = Histogram(
    'faceit_analysis_duration_seconds', 'Analysis duration'
)
ACTIVE_USERS = Counter('faceit_active_users', 'Active user sessions')


@app.get("/metrics")
async def metrics():
    return Response(generate_latest())
