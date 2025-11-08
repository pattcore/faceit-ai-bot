from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional, Dict
from .service import PaymentService
from .models import (
    PaymentRequest,
    PaymentResponse,
    PaymentStatus,
    PaymentProvider,
    REGION_PAYMENT_CONFIG,
    RegionPaymentMethods
)
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["payments"])


def get_payment_service() -> PaymentService:
    """Dependency для получения сервиса платежей"""
    return PaymentService(settings)

@router.get("/methods/{region}")
async def get_payment_methods(region: str) -> RegionPaymentMethods:
    """
    Получение доступных способов оплаты для региона
    """
    if region not in REGION_PAYMENT_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported region: {region}"
        )
    return REGION_PAYMENT_CONFIG[region]

@router.post("/create", response_model=PaymentResponse)
async def create_payment(
    request: PaymentRequest,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Создание нового платежа
    """
    return await payment_service.create_payment(request)

@router.get("/status/{payment_id}")
async def check_payment_status(
    payment_id: str,
    provider: PaymentProvider,
    payment_service: PaymentService = Depends(get_payment_service)
) -> PaymentStatus:
    """
    Check payment status
    """
    return await payment_service.check_payment_status(payment_id, provider)

@router.post("/webhook/sbp")
async def sbp_webhook(
    data: Dict,
    signature: Optional[str] = Header(None),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Вебхук для СБП платежей
    """
    await payment_service.process_webhook(PaymentProvider.SBP, data)
    return {"status": "success"}

@router.post("/webhook/yookassa")
async def yookassa_webhook(
    data: Dict,
    signature: Optional[str] = Header(None),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Вебхук для ЮKassa платежей
    """
    await payment_service.process_webhook(PaymentProvider.YOOKASSA, data)
    return {"status": "success"}

@router.post("/webhook/qiwi")
async def qiwi_webhook(
    data: Dict,
    signature: Optional[str] = Header(None),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Вебхук для QIWI платежей
    """
    await payment_service.process_webhook(PaymentProvider.QIWI, data)
    return {"status": "success"}