import logging
from typing import Optional, Dict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session

from ...auth.dependencies import get_current_active_user
from ...config.settings import settings
from ...database.connection import get_db
from ...database.models import User, Payment as DBPayment, SubscriptionTier as DBSubscriptionTier
from ...services.captcha_service import captcha_service
from ...core.structured_logging import business_logger
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    payment_service: PaymentService = Depends(get_payment_service),
) -> PaymentResponse:
    """Create new payment for the current authenticated user.

    Performs CAPTCHA verification, creates a payment via the selected provider
    (or returns a mock response if providers are not configured), and then
    stores the payment in the database linked to the user and subscription tier.
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

    # user_id is always taken from the current user, not from the request body
    payment_request.user_id = str(current_user.id)

    # Create payment via service (real or mock depending on settings)
    payment_response = await payment_service.create_payment(payment_request)

    # Try to map the requested subscription tier to DB enum
    db_subscription_tier = None
    if payment_request.subscription_tier:
        try:
            db_subscription_tier = DBSubscriptionTier(
                payment_request.subscription_tier.lower()
            )
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid subscription tier: {payment_request.subscription_tier}",
            )

    # Store payment in DB for further webhook processing
    db_payment = DBPayment(
        user_id=current_user.id,
        amount=payment_response.amount,
        currency=payment_response.currency.value
        if isinstance(payment_response.currency, Currency)
        else str(payment_response.currency),
        provider=payment_request.provider.value,
        provider_payment_id=payment_response.payment_id,
        subscription_tier=db_subscription_tier,
        description=payment_request.description,
    )

    db.add(db_payment)
    db.commit()

    # Business audit log for created payment (initially pending)
    try:
        business_logger.log_payment_event(
            user_id=str(current_user.id),
            amount=db_payment.amount,
            currency=str(db_payment.currency),
            status="pending",
            payment_id=str(db_payment.provider_payment_id),
            provider=str(db_payment.provider) if db_payment.provider is not None else None,
        )
    except Exception:
        # Do not break API flow if logging fails
        logger.exception("Failed to log payment creation event")

    return payment_response


@router.get("/status/{payment_id}")
async def check_payment_status(
    payment_id: str,
    provider: PaymentProvider,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    payment_service: PaymentService = Depends(get_payment_service),
) -> PaymentStatus:
    """Check payment status for the current authenticated user.

    Only allows checking status for payments that belong to the current user.
    """
    db_payment = (
        db.query(DBPayment)
        .filter(
            DBPayment.provider_payment_id == payment_id,
            DBPayment.user_id == current_user.id,
        )
        .first()
    )

    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return await payment_service.check_payment_status(payment_id, provider)


@router.post("/webhook/sbp")
async def sbp_webhook(
    data: Dict,
    signature: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """Webhook for SBP payments"""
    # In production validate webhook secret if it is configured
    if not settings.TEST_ENV and settings.SBP_WEBHOOK_SECRET:
        if not signature or signature != settings.SBP_WEBHOOK_SECRET:
            logger.warning("Invalid SBP webhook signature")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    await payment_service.process_webhook(PaymentProvider.SBP, data, db)
    return {"status": "success"}


@router.post("/webhook/yookassa")
async def yookassa_webhook(
    data: Dict,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """Webhook for YooKassa payments"""
    if not settings.TEST_ENV:
        if not settings.YOOKASSA_SHOP_ID or not settings.YOOKASSA_SECRET_KEY:
            logger.warning("YooKassa webhook called but credentials not configured")
            raise HTTPException(status_code=503, detail="Payment provider not configured")

        import base64

        credentials = f"{settings.YOOKASSA_SHOP_ID}:{settings.YOOKASSA_SECRET_KEY}"
        expected = "Basic " + base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

        if authorization != expected:
            logger.warning("Invalid YooKassa webhook authorization header")
            raise HTTPException(status_code=401, detail="Invalid webhook authorization")

    await payment_service.process_webhook(PaymentProvider.YOOKASSA, data, db)
    return {"status": "success"}


@router.post("/webhook/qiwi")
async def qiwi_webhook(
    data: Dict,
    signature: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """Webhook for QIWI payments (not yet implemented in service)."""
    await payment_service.process_webhook(PaymentProvider.QIWI, data, db)
    return {"status": "success"}
