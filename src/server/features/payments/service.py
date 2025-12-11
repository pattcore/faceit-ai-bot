from typing import Dict, Optional, Any, cast
from fastapi import HTTPException
import httpx
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from prometheus_client import Counter, Histogram
from ...database.models import (
    Payment as DBPayment,
    PaymentStatus as DBPaymentStatus,
    Subscription as DBSubscription,
    SubscriptionTier as DBSubscriptionTier,
)
from ...core.structured_logging import business_logger
from .models import (
    PaymentRequest,
    PaymentResponse,
    PaymentStatus,
    PaymentProvider,
    Currency,
    REGION_PAYMENT_CONFIG,
)

logger = logging.getLogger(__name__)

PAYMENT_CREATE_TOTAL = Counter(
    "payment_create_total",
    "Total payment create attempts",
    ["provider"],
)

PAYMENT_CREATE_FAILED_TOTAL = Counter(
    "payment_create_failed_total",
    "Total failed payment create attempts",
    ["provider"],
)

PAYMENT_CREATE_DURATION_SECONDS = Histogram(
    "payment_create_duration_seconds",
    "Payment creation duration in seconds",
    ["provider"],
)

PAYMENT_WEBHOOK_COMPLETED_TOTAL = Counter(
    "payment_webhook_completed_total",
    "Total successfully completed payments via webhooks",
    ["provider"],
)

PAYMENT_WEBHOOK_FAILED_TOTAL = Counter(
    "payment_webhook_failed_total",
    "Total payment webhook processing errors",
    ["provider"],
)

PAYMENT_WEBHOOK_DURATION_SECONDS = Histogram(
    "payment_webhook_duration_seconds",
    "Payment webhook processing duration in seconds",
    ["provider"],
)


class PaymentService:
    def __init__(self, settings):
        self.settings = settings
        # Register only providers that have implemented handlers
        self.providers = {
            PaymentProvider.SBP: self._process_sbp_payment,
            PaymentProvider.YOOKASSA: self._process_yookassa_payment,
        }

    async def create_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Create payment through selected payment system"""
        provider_label = getattr(getattr(request, "provider", None), "value", str(getattr(request, "provider", "unknown")))
        try:
            with PAYMENT_CREATE_DURATION_SECONDS.labels(provider=provider_label).time():
                if request.provider not in self.providers:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unsupported payment provider: {request.provider}"
                    )

                # Check payment method availability for region
                self._validate_payment_method(request)

                try:
                    PAYMENT_CREATE_TOTAL.labels(provider=provider_label).inc()
                except Exception:
                    logger.exception("Failed to increment payment create metric")

                # Process payment through corresponding provider
                return await self.providers[request.provider](request)
        except HTTPException:
            # Не заворачиваем уже сформированные HTTP ошибки (например, 4xx)
            # в общий 500, чтобы клиент получал корректный статус.
            raise
        except Exception as e:
            try:
                PAYMENT_CREATE_FAILED_TOTAL.labels(provider=provider_label).inc()
            except Exception:
                logger.exception("Failed to increment failed payment create metric")

            logger.exception(f"Payment creation failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Payment creation failed"
            )

    async def check_payment_status(
        self,
        payment_id: str,
        provider: PaymentProvider
    ) -> PaymentStatus:
        """Check payment status"""
        try:
            if provider == PaymentProvider.SBP:
                return await self._check_sbp_status(payment_id)
            elif provider == PaymentProvider.YOOKASSA:
                return await self._check_yookassa_status(payment_id)
            # ... other providers

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported payment provider "
                    f"for status check: {provider}"
                )
            )
        except HTTPException:
            # Сохраняем оригинальный HTTP статус (например, 400)
            # вместо заворачивания его в общий 500.
            raise
        except Exception as e:
            logger.exception(
                f"Payment status check failed: {str(e)}"
            )
            raise HTTPException(
                status_code=500,
                detail="Payment status check failed"
            )

    async def _check_sbp_status(self, payment_id: str) -> PaymentStatus:
        """Check SBP payment status.

        Пока внешний статус-чекер не реализован, явно сообщаем об отсутствии
        поддержки вместо падения с AttributeError.
        """
        raise HTTPException(
            status_code=400,
            detail=f"Status check for provider SBP is not implemented (payment_id={payment_id})",
        )

    async def _check_yookassa_status(self, payment_id: str) -> PaymentStatus:
        """Check YooKassa payment status.

        Аналогично SBP, пока статус не запрашивается у внешнего API, отвечаем 400.
        """
        raise HTTPException(
            status_code=400,
            detail=f"Status check for provider YooKassa is not implemented (payment_id={payment_id})",
        )

    async def _process_sbp_payment(
        self, request: PaymentRequest
    ) -> PaymentResponse:
        """Process payment through SBP"""
        try:
            # If SBP is not configured, return mock payment response
            if not self.settings.SBP_API_URL or not self.settings.SBP_TOKEN:
                logger.warning(
                    "SBP settings are not configured. "
                    "Returning mock payment response instead of calling external SBP API."
                )
                now = datetime.now()
                return PaymentResponse(
                    payment_id=f"mock_{request.user_id}_{int(now.timestamp())}",
                    status="pending",
                    payment_url=f"{self.settings.WEBSITE_URL}/payment/success?subscription={request.subscription_tier}",
                    amount=request.amount,
                    currency=request.currency,
                    created_at=now,
                    expires_at=now + timedelta(minutes=15),
                    confirmation_type="redirect",
                )
            headers = {
                "Authorization": f"Bearer {self.settings.SBP_TOKEN}",
                "Content-Type": "application/json"
            }

            payload = {
                "amount": {
                    "value": str(request.amount),
                    "currency": request.currency.value
                },
                "description": request.description,
                "subscription_id": request.subscription_tier,
                "user_id": request.user_id,
                "return_url": f"{self.settings.WEBSITE_URL}/payment/success",
                "webhook_url": f"{self.settings.API_URL}/payments/webhook/sbp",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.settings.SBP_API_URL}/v1/payments",
                    headers=headers,
                    json=payload,
                    timeout=10.0
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"SBP payment failed: {response.text}"
                    )

                data = response.json()
                return PaymentResponse(
                    payment_id=data["payment_id"],
                    status=data["status"],
                    payment_url=data["payment_url"],
                    amount=request.amount,
                    currency=request.currency,
                    created_at=datetime.now(),
                    expires_at=datetime.now() + timedelta(minutes=15),
                    confirmation_type="qr"
                )

        except Exception:
            logger.exception("SBP payment processing failed")
            raise

    async def _process_yookassa_payment(
        self, request: PaymentRequest
    ) -> PaymentResponse:
        """Process payment via YooKassa"""
        try:
            # If YooKassa is not configured, return mock payment response
            if not self.settings.YOOKASSA_SHOP_ID or not self.settings.YOOKASSA_SECRET_KEY:
                logger.warning(
                    "YooKassa settings are not configured. "
                    "Returning mock payment response instead of calling external YooKassa API."
                )
                now = datetime.now()
                return PaymentResponse(
                    payment_id=f"mock_{request.user_id}_{int(now.timestamp())}",
                    status="pending",
                    payment_url=(
                        f"{self.settings.WEBSITE_URL}/payment/success?subscription="
                        f"{request.subscription_tier}"
                    ),
                    amount=request.amount,
                    currency=request.currency,
                    created_at=now,
                    expires_at=now + timedelta(minutes=15),
                    confirmation_type="redirect",
                )

            # Basic auth: shop_id:secret_key
            import base64

            credentials = f"{self.settings.YOOKASSA_SHOP_ID}:{self.settings.YOOKASSA_SECRET_KEY}"
            encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

            headers = {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/json",
                "Idempotence-Key": (
                    f"{request.user_id}_{datetime.now().timestamp()}"
                ),
            }

            payload = {
                "amount": {
                    "value": str(request.amount),
                    "currency": request.currency.value
                },
                "description": request.description,
                "metadata": {
                    "subscription_tier": request.subscription_tier,
                    "user_id": request.user_id
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": (
                        f"{self.settings.WEBSITE_URL}/payment/success"
                    )
                },
                "capture": True,
                "payment_method_data": {
                    "type": request.payment_method
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.settings.YOOKASSA_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=10.0
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"YooKassa payment failed: {response.text}"
                    )

                data = response.json()
                return PaymentResponse(
                    payment_id=data["id"],
                    status=data["status"],
                    payment_url=data["confirmation"]["confirmation_url"],
                    amount=float(data["amount"]["value"]),
                    currency=Currency(data["amount"]["currency"]),
                    created_at=datetime.fromisoformat(data["created_at"]),
                    expires_at=datetime.now() + timedelta(days=1),
                    confirmation_type="redirect"
                )

        except Exception:
            logger.exception("YooKassa payment processing failed")
            raise

    def _validate_payment_method(self, request: PaymentRequest):
        """Check payment method availability for region"""
        region = self._detect_region(request)
        region_config = REGION_PAYMENT_CONFIG.get(region)

        if not region_config:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported region: {region}"
            )

        if request.payment_method not in region_config.available_methods:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Payment method {request.payment_method} "
                    f"is not available in region {region}"
                )
            )

        if request.provider not in region_config.enabled_providers:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Payment provider {request.provider} "
                    f"is not available in region {region}"
                )
            )

    def _detect_region(self, request: PaymentRequest) -> str:
        """Detect user region"""
        # Region detection not implemented
        if request.currency == Currency.RUB:
            return "RU"
        elif request.currency == Currency.USD:
            return "US"
        elif request.currency == Currency.EUR:
            return "EU"
        else:
            return "US"  # Default value

    async def process_webhook(
        self,
        provider: PaymentProvider,
        data: Dict,
        db: Session,
    ) -> None:
        """Process webhooks from payment systems"""
        provider_label = getattr(provider, "value", str(provider))
        try:
            with PAYMENT_WEBHOOK_DURATION_SECONDS.labels(provider=provider_label).time():
                if provider == PaymentProvider.SBP:
                    await self._handle_sbp_webhook(data, db)
                elif provider == PaymentProvider.YOOKASSA:
                    await self._handle_yookassa_webhook(data, db)
                # ... other providers
        except Exception as e:
            try:
                PAYMENT_WEBHOOK_FAILED_TOTAL.labels(provider=provider_label).inc()
            except Exception:
                logger.exception("Failed to increment failed webhook metric")

            logger.exception(f"Webhook processing failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Webhook processing failed"
            )

    async def _handle_sbp_webhook(self, data: Dict, db: Session) -> None:
        """Handle SBP webhook: update payment and subscription state in DB."""
        payment_id = data.get("payment_id") or data.get("id")
        if not payment_id:
            raise ValueError("SBP webhook payload missing payment_id")

        db_payment: Optional[DBPayment] = (
            db.query(DBPayment)
            .filter(DBPayment.provider_payment_id == str(payment_id))
            .first()
        )
        if not db_payment:
            logger.warning("SBP webhook for unknown payment_id=%s", payment_id)
            return

        amount_info = data.get("amount") or {}
        raw_value: Any = amount_info.get("value")
        amount_value: Optional[float]
        if isinstance(raw_value, (int, float, str)):
            try:
                amount_value = float(raw_value)
            except (TypeError, ValueError):
                amount_value = None
        else:
            amount_value = None
        currency_code = amount_info.get("currency")

        # Validate amount and currency if present
        if amount_value is not None and abs(db_payment.amount - amount_value) > 0.01:
            logger.warning(
                "SBP webhook amount mismatch for payment_id=%s: expected=%s got=%s",
                payment_id,
                db_payment.amount,
                amount_value,
            )
            return

        if currency_code and db_payment.currency and db_payment.currency.upper() != str(currency_code).upper():
            logger.warning(
                "SBP webhook currency mismatch for payment_id=%s: expected=%s got=%s",
                payment_id,
                db_payment.currency,
                currency_code,
            )
            return

        status = data.get("status")
        if status not in {"paid", "succeeded", "completed"}:
            logger.info(
                "Ignoring SBP webhook with non-final status: payment_id=%s status=%s",
                payment_id,
                status,
            )
            return

        # Idempotency: do nothing if already completed
        if db_payment.status == DBPaymentStatus.COMPLETED:
            logger.info(
                "SBP webhook for already completed payment_id=%s, skipping",
                payment_id,
            )
            return

        db_payment.status = DBPaymentStatus.COMPLETED  # type: ignore[assignment]
        db_payment.completed_at = datetime.utcnow()  # type: ignore[assignment]

        # Extend or create subscription based on stored subscription_tier
        tier = db_payment.subscription_tier
        if tier is not None:
            now = datetime.utcnow()
            subscription: Optional[DBSubscription] = (
                db.query(DBSubscription)
                .filter(DBSubscription.user_id == db_payment.user_id)
                .first()
            )

            if (
                subscription
                and subscription.is_active
                and subscription.expires_at is not None
                and subscription.expires_at > now
            ):
                # Extend existing active subscription
                subscription.expires_at = subscription.expires_at + timedelta(days=30)  # type: ignore[assignment]
                subscription.tier = tier
            elif subscription:
                # Reactivate / reset existing subscription
                subscription.started_at = now  # type: ignore[assignment]
                subscription.expires_at = now + timedelta(days=30)  # type: ignore[assignment]
                subscription.is_active = True  # type: ignore[assignment]
                subscription.tier = tier
            else:
                # Create new subscription
                subscription = DBSubscription(
                    user_id=db_payment.user_id,
                    tier=tier,
                    started_at=now,
                    expires_at=now + timedelta(days=30),
                    is_active=True,
                )
                db.add(subscription)

        db.commit()

        # Business audit log for completed payment via SBP
        try:
            business_logger.log_payment_event(
                user_id=str(db_payment.user_id),
                amount=cast(float, db_payment.amount),
                currency=str(db_payment.currency) if db_payment.currency is not None else "",
                status="completed",
                payment_id=str(db_payment.provider_payment_id),
                provider=str(db_payment.provider) if db_payment.provider is not None else None,
            )
        except Exception:
            logger.exception("Failed to log SBP payment completion event")

        try:
            PAYMENT_WEBHOOK_COMPLETED_TOTAL.labels(provider=PaymentProvider.SBP.value).inc()
        except Exception:
            logger.exception("Failed to increment SBP webhook completed metric")

    async def _handle_yookassa_webhook(self, data: Dict, db: Session) -> None:
        """Handle YooKassa webhook: update payment and subscription state in DB."""
        payment_obj = data.get("object") or data
        payment_id = payment_obj.get("id")
        if not payment_id:
            raise ValueError("YooKassa webhook payload missing id")

        db_payment: Optional[DBPayment] = (
            db.query(DBPayment)
            .filter(DBPayment.provider_payment_id == str(payment_id))
            .first()
        )
        if not db_payment:
            logger.warning("YooKassa webhook for unknown payment_id=%s", payment_id)
            return

        amount_info = payment_obj.get("amount") or {}
        raw_value: Any = amount_info.get("value")
        amount_value: Optional[float]
        if isinstance(raw_value, (int, float, str)):
            try:
                amount_value = float(raw_value)
            except (TypeError, ValueError):
                amount_value = None
        else:
            amount_value = None
        currency_code = amount_info.get("currency")

        # Validate amount and currency if present
        if amount_value is not None and abs(db_payment.amount - amount_value) > 0.01:
            logger.warning(
                "YooKassa webhook amount mismatch for payment_id=%s: expected=%s got=%s",
                payment_id,
                db_payment.amount,
                amount_value,
            )
            return

        if currency_code and db_payment.currency and db_payment.currency.upper() != str(currency_code).upper():
            logger.warning(
                "YooKassa webhook currency mismatch for payment_id=%s: expected=%s got=%s",
                payment_id,
                db_payment.currency,
                currency_code,
            )
            return

        status = payment_obj.get("status")
        if status != "succeeded":
            logger.info(
                "Ignoring YooKassa webhook with non-succeeded status: payment_id=%s status=%s",
                payment_id,
                status,
            )
            return

        # Idempotency: do nothing if already completed
        if db_payment.status == DBPaymentStatus.COMPLETED:
            logger.info(
                "YooKassa webhook for already completed payment_id=%s, skipping",
                payment_id,
            )
            return

        db_payment.status = DBPaymentStatus.COMPLETED  # type: ignore[assignment]
        db_payment.completed_at = datetime.utcnow()  # type: ignore[assignment]

        # Extend or create subscription based on stored subscription_tier
        tier = db_payment.subscription_tier
        if tier is None:
            # Fallback to metadata from webhook if present
            metadata = payment_obj.get("metadata") or {}
            tier_raw = metadata.get("subscription_tier")
            if tier_raw:
                try:
                    tier = DBSubscriptionTier(tier_raw.lower())
                    db_payment.subscription_tier = tier
                except ValueError:
                    logger.warning(
                        "Invalid subscription_tier in YooKassa metadata for payment_id=%s: %s",
                        payment_id,
                        tier_raw,
                    )

        if tier is not None:
            now = datetime.utcnow()
            subscription: DBSubscription | None = (
                db.query(DBSubscription)
                .filter(DBSubscription.user_id == db_payment.user_id)
                .first()
            )

            if (
                subscription
                and subscription.is_active
                and subscription.expires_at is not None
                and subscription.expires_at > now
            ):
                subscription.expires_at = subscription.expires_at + timedelta(days=30)  # type: ignore[assignment]
                subscription.tier = tier
            elif subscription:
                subscription.started_at = now  # type: ignore[assignment]
                subscription.expires_at = now + timedelta(days=30)  # type: ignore[assignment]
                subscription.is_active = True  # type: ignore[assignment]
                subscription.tier = tier
            else:
                subscription = DBSubscription(
                    user_id=db_payment.user_id,
                    tier=tier,
                    started_at=now,
                    expires_at=now + timedelta(days=30),
                    is_active=True,
                )
                db.add(subscription)

        db.commit()

        # Business audit log for completed payment via YooKassa
        try:
            business_logger.log_payment_event(
                user_id=str(db_payment.user_id),
                amount=cast(float, db_payment.amount),
                currency=str(db_payment.currency) if db_payment.currency is not None else "",
                status="completed",
                payment_id=str(db_payment.provider_payment_id),
                provider=str(db_payment.provider) if db_payment.provider is not None else None,
            )
        except Exception:
            logger.exception("Failed to log YooKassa payment completion event")

        try:
            PAYMENT_WEBHOOK_COMPLETED_TOTAL.labels(provider=PaymentProvider.YOOKASSA.value).inc()
        except Exception:
            logger.exception("Failed to increment YooKassa webhook completed metric")
