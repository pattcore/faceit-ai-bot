from typing import Optional, Dict
from fastapi import HTTPException
import httpx
import logging
import json
import hmac
import hashlib
from datetime import datetime, timedelta
from .models import (
    PaymentRequest,
    PaymentResponse,
    PaymentStatus,
    PaymentProvider,
    PaymentMethod,
    Currency,
    REGION_PAYMENT_CONFIG
)

logger = logging.getLogger(__name__)

class PaymentService:
    def __init__(self, settings):
        self.settings = settings
        self.providers = {
            PaymentProvider.SBP: self._process_sbp_payment,
            PaymentProvider.YOOKASSA: self._process_yookassa_payment,
            PaymentProvider.QIWI: self._process_qiwi_payment,
            PaymentProvider.STRIPE: self._process_stripe_payment,
            PaymentProvider.PAYPAL: self._process_paypal_payment,
            PaymentProvider.CRYPTO: self._process_crypto_payment
        }

    async def create_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Создание платежа через выбранную платежную систему"""
        try:
            if request.provider not in self.providers:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported payment provider: {request.provider}"
                )

            # Проверяем доступность метода оплаты для региона
            self._validate_payment_method(request)

            # Обработка платежа через соответствующий провайдер
            return await self.providers[request.provider](request)

        except Exception as e:
            logger.exception(f"Payment creation failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Payment creation failed: {str(e)}"
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
            # ... другие провайдеры

            raise HTTPException(
                status_code=400,
                detail=f"Unsupported payment provider for status check: {provider}"
            )

        except Exception as e:
            logger.exception(f"Payment status check failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Payment status check failed: {str(e)}"
            )

    async def _process_sbp_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Обработка платежа через СБП"""
        try:
            headers = {
                "Authorization": f"Bearer {self.settings.SBP_TOKEN}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "amount": {
                    "value": str(request.amount),
                    "currency": request.currency
                },
                "description": request.description,
                "subscription_id": request.subscription_tier,
                "user_id": request.user_id,
                "return_url": f"{self.settings.WEBSITE_URL}/payment/success",
                "webhook_url": f"{self.settings.API_URL}/webhooks/sbp"
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

        except Exception as e:
            logger.exception("SBP payment processing failed")
            raise

    async def _process_yookassa_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Обработка платежа через ЮKassa"""
        try:
            headers = {
                "Authorization": f"Basic {self.settings.YOOKASSA_AUTH}",
                "Content-Type": "application/json",
                "Idempotence-Key": f"{request.user_id}_{datetime.now().timestamp()}"
            }

            payload = {
                "amount": {
                    "value": str(request.amount),
                    "currency": request.currency
                },
                "description": request.description,
                "metadata": {
                    "subscription_tier": request.subscription_tier,
                    "user_id": request.user_id
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": f"{self.settings.WEBSITE_URL}/payment/success"
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

        except Exception as e:
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
                detail=f"Payment method {request.payment_method} is not available in region {region}"
            )

        if request.provider not in region_config.enabled_providers:
            raise HTTPException(
                status_code=400,
                detail=f"Payment provider {request.provider} is not available in region {region}"
            )

    def _detect_region(self, request: PaymentRequest) -> str:
        """Определение региона пользователя"""
        # Region detection not implemented
        if request.currency == Currency.RUB:
            return "RU"
        elif request.currency == Currency.USD:
            return "US"
        elif request.currency == Currency.EUR:
            return "EU"
        else:
            return "US"  # значение по умолчанию

    async def process_webhook(self, provider: PaymentProvider, data: Dict) -> None:
        """Обработка вебхуков от платежных систем"""
        try:
            if provider == PaymentProvider.SBP:
                await self._handle_sbp_webhook(data)
            elif provider == PaymentProvider.YOOKASSA:
                await self._handle_yookassa_webhook(data)
            # ... другие провайдеры
        except Exception as e:
            logger.exception(f"Webhook processing failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Webhook processing failed: {str(e)}"
            )