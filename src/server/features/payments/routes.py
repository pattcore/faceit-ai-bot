import logging
from typing import Optional, Dict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Header, Request

from ...config.settings import settings
from ...services.captcha_service import captcha_service
from .service import PaymentService
from .models import (
    PaymentRequest,
    PaymentResponse,
    PaymentStatus,
    PaymentProvider,
    REGION_PAYMENT_CONFIG,
    RegionPaymentMethods,
    Currency,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["payments"])


def get_payment_service() -> PaymentService:
    """Dependency for payment service"""
    return PaymentService(settings)


@router.get("/methods/{region}")
async def get_payment_methods(region: str) -> RegionPaymentMethods:
    """
    Get available payment methods for region
    """
    if region not in REGION_PAYMENT_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported region: {region}"
        )
    return REGION_PAYMENT_CONFIG[region]


@router.post("/create", response_model=PaymentResponse)
async def create_payment(
    payment_request: PaymentRequest,
    request: Request,
) -> PaymentResponse:
    """Create new payment (mock for pattmsc.online).

    На тестовом стенде не ходим во внешние платёжки, а сразу
    возвращаем платёж с редиректом на страницу успеха.
    """
    remote_ip = request.client.host if request.client else None
    captcha_ok = await captcha_service.verify_token(
        token=payment_request.captcha_token,
        remote_ip=remote_ip,
        action="payment_create",
    )
    if not captcha_ok:
        raise HTTPException(
            status_code=400,
            detail="CAPTCHA verification failed",
        )

    now = datetime.utcnow()
    return PaymentResponse(
        payment_id=f"mock_{payment_request.user_id}_{int(now.timestamp())}",
        status="pending",
        payment_url=f"https://pattmsc.online/payment/success?subscription={payment_request.subscription_tier}",
        amount=payment_request.amount,
        currency=Currency(payment_request.currency),
        created_at=now,
        expires_at=now + timedelta(minutes=15),
        confirmation_type="redirect",
    )


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
    Webhook for SBP payments
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
    Webhook for YooKassa payments
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
    Webhook for QIWI payments
    """
    await payment_service.process_webhook(PaymentProvider.QIWI, data)
    return {"status": "success"}
