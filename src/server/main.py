from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import settings
from exceptions import BaseAPIException

# Import routers
from features.demo_analyzer.routes import router as demo_router
from features.payments.routes import router as payments_router
from features.subscriptions.routes import router as subscriptions_router
from features.teammates.routes import router as teammates_router
from features.ai_analysis.routes import router as ai_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    debug=False,
    docs_url="/docs",
    redoc_url="/redoc"
)

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
@app.exception_handler(BaseAPIException)
async def api_exception_handler(request: Request, exc: BaseAPIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "error_code": exc.error_code,
            "path": request.url.path
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "path": request.url.path
        }
    )

# Include routers
app.include_router(demo_router)
app.include_router(payments_router)
app.include_router(subscriptions_router)
app.include_router(teammates_router)
app.include_router(ai_router)

@app.get("/", tags=["health"])
def root():
    return {"message": "Faceit AI Bot service running", "status": "healthy"}

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy", "service": "backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)