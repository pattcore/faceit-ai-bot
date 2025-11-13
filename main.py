from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import os
import logging
import requests
import sys

# Add src path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

app = FastAPI(
    title="Faceit Bot API Service",
    version="0.3.0",
    description="API for CS2 player analysis on Faceit platform"
)

# Configure CORS for development and production
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
]

# Allow all origins in development
if os.getenv("NODE_ENV") == "development":
    origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Connect middleware
try:
    from src.server.middleware.rate_limiter import rate_limiter

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        # Skip health check
        if request.url.path in [
            "/", "/health", "/docs", "/redoc", "/openapi.json"
        ]:
            return await call_next(request)

        # Check rate limit
        await rate_limiter(request)
        return await call_next(request)

    logging.info("Rate limiter enabled")
except Exception as e:
    logging.warning(f"Could not load rate limiter: {e}")

# Connect routers
try:
    from src.server.features.player_analysis import router as player_router
    app.include_router(player_router)
    logging.info("Player analysis router loaded successfully")
except Exception as e:
    logging.warning(f"Could not load player analysis router: {e}")

# Model loading commented out - uncomment when needed
# import torch
# from torchvision import transforms
# from PIL import Image
# model = torch.hub.load('pytorch/vision:v0.10.0', 'resnet18', pretrained=True)
# model.eval()
# transform = transforms.Compose([
#     transforms.Resize((224, 224)),
#     transforms.ToTensor(),
#     transforms.Normalize(
#         mean=[0.485, 0.456, 0.406],
#         std=[0.229, 0.224, 0.225]
#     ),
# ])


@app.get("/")
def root():
    return {
        "message": "Faceit Bot API service running",
        "status": "healthy"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "analysis"}


@app.post("/public/demo-analysis")
async def public_demo_analysis(request: dict):
    """
    Public demo analysis endpoint (no auth required)
    """
    try:
        nickname = request.get("nickname", "test_player")
        
        # Mock analysis result
        return {
            "nickname": nickname,
            "status": "completed",
            "analysis": {
                "kd_ratio": 1.25,
                "win_rate": 65.5,
                "headshot_percentage": 48.2,
                "avg_kills": 18.5,
                "avg_deaths": 14.8
            },
            "strengths": ["aim", "positioning", "clutch_ability"],
            "weaknesses": ["consistency", "economy_management"],
            "recommendations": [
                "Practice crosshair placement daily",
                "Study professional demos",
                "Work on economy decisions"
            ],
            "training_plan": {
                "daily_routine": [
                    {"exercise": "Aim training", "duration": "30 min"},
                    {"exercise": "Demo review", "duration": "20 min"},
                    {"exercise": "Deathmatch", "duration": "15 min"}
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-demo")
async def analyze_demo(demo: UploadFile = File(...)):
    """
    CS2 demo file analysis and statistics extraction
    """
    if not demo.filename.endswith('.dem'):
        return {"error": "Invalid file format. Only .dem files are supported"}

    # Demo analysis stub
    try:
        return {
            "filename": demo.filename,
            "status": "pending",
            "message": "Demo analysis not implemented",
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/generate-training")
async def generate_training(user_stats: dict):
    """
    Generate personalized training plan
    """
    # Mock training plan
    mock_training_plan = {
        "player_level": "intermediate",
        "focus_areas": ["aim", "positioning", "game_sense"],
        "daily_exercises": [
            {
                "name": "Aim Training - Headshot Only",
                "duration": 30,
                "description": "Headshot accuracy training on aim_botz"
            },
            {
                "name": "Crosshair Placement",
                "duration": 20,
                "description": "Crosshair placement practice"
            },
            {
                "name": "Spray Control",
                "duration": 25,
                "description": "Spray control practice for AK-47 and M4A4"
            }
        ],
        "weekly_goals": [
            "Increase accuracy by 5%",
            "Reduce deaths from behind by 20%",
            "Improve K/D ratio to 1.3"
        ],
        "estimated_improvement_time": "2-3 weeks"
    }

    return mock_training_plan


@app.get("/voice-assistant/commands")
async def get_voice_commands():
    """
    Get available voice commands
    """
    commands = {
        "available_commands": [
            {
                "command": "analyze round",
                "description": "Analyze current round"
            },
            {
                "command": "team strategy",
                "description": "Team strategy recommendations"
            },
            {"command": "economy advice", "description": "Economy advice"},
            {"command": "position check", "description": "Position check"},
            {"command": "utility usage", "description": "Utility usage advice"}
        ],
        "languages_supported": ["ru", "en"],
        "status": "active"
    }

    return commands

# Voice command processing not implemented yet


# Payment models
class PaymentRequest(BaseModel):
    amount: float
    currency: str
    description: str

    @validator("amount")
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

    @validator("currency")
    def validate_currency(cls, v):
        allowed_currencies = ["RUB", "USD", "EUR"]
        if v not in allowed_currencies:
            raise ValueError(f"Currency must be one of {allowed_currencies}")
        return v


class PaymentResponse(BaseModel):
    payment_url: str
    status: str


# YooKassa integration
YOOKASSA_API_URL = "https://api.yookassa.ru/v3/payments"
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def disable_auth_dependency(request: Request):
    test_env = os.getenv("TEST_ENV")
    if test_env == "true":
        return
    raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/payments/yookassa", response_model=PaymentResponse)
def create_yookassa_payment(payment: PaymentRequest):
    if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="YooKassa credentials not configured"
        )

    headers = {
        "Content-Type": "application/json",
    }
    auth = (YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY)
    data = {
        "amount": {
            "value": f"{payment.amount:.2f}",
            "currency": payment.currency,
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "http://localhost:3000/payment-success",
        },
        "description": payment.description,
    }

    try:
        response = requests.post(
            YOOKASSA_API_URL,
            json=data,
            headers=headers,
            auth=auth,
            timeout=10
        )

        if response.status_code != 200:
            error_detail = (
                response.json()
                if response.content
                else {"error": "Unknown error"}
            )
            raise HTTPException(
                status_code=response.status_code,
                detail=error_detail
            )

        payment_data = response.json()
        return PaymentResponse(
            payment_url=payment_data["confirmation"]["confirmation_url"],
            status=payment_data["status"],
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"YooKassa API error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Payment service unavailable"
        )


# SBP integration
SBP_API_URL = os.getenv("SBP_API_URL", "")
SBP_TOKEN = os.getenv("SBP_TOKEN", "")


@app.post("/payments/sbp", response_model=PaymentResponse)
def create_sbp_payment_stub(payment: PaymentRequest):
    return PaymentResponse(
        payment_url="https://sbp-payment.ru/pay",
        status="pending",
    )


@app.middleware("http")
async def log_request_middleware(request: Request, call_next):
    response = await call_next(request)
    return response
