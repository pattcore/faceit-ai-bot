from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging
import requests

app = FastAPI(title="Faceit AI Bot Service", version="0.2.0")

# Configure CORS for development and production
origins = [
    "http://localhost:5000",
    "http://localhost:4000",
    "https://89f4cd76-9b36-4cb9-9797-f7bf95690841-00-3isporgvi3p56.picard.replit.dev",
]

# Allow all Replit domains in development
if os.getenv("NODE_ENV") == "development" or os.getenv("REPLIT_DEV_DOMAIN"):
    origins.append("*")  # Allow all origins in development

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ML model loading commented out - uncomment when needed
# import torch
# from torchvision import transforms
# from PIL import Image
# model = torch.hub.load('pytorch/vision:v0.10.0', 'resnet18', pretrained=True)
# model.eval()
# transform = transforms.Compose([
#     transforms.Resize((224, 224)),
#     transforms.ToTensor(),
#     transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
# ])

@app.get("/")
def root():
    return {"message": "Faceit AI Bot service running", "status": "healthy"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "ai-ml"}

@app.post("/analyze-demo")
async def analyze_demo(demo: UploadFile = File(...)):
    """
    Анализ демки CS2 с использованием модели машинного обучения
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
            {"command": "analyze round", "description": "Analyze current round"},
            {"command": "team strategy", "description": "Team strategy recommendations"},
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

    response = requests.post(YOOKASSA_API_URL, json=data, headers=headers, auth=auth)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    payment_data = response.json()
    return PaymentResponse(
        payment_url=payment_data["confirmation"]["confirmation_url"],
        status=payment_data["status"],
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
