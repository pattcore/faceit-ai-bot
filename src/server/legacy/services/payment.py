import httpx
from fastapi import HTTPException
from ..config.settings import settings
from ..models.payment import PaymentRequest, PaymentResponse
import logging

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self):
        self.yookassa_url = settings.YOOKASSA_API_URL
        self.yookassa_shop_id = settings.YOOKASSA_SHOP_ID
        self.yookassa_secret_key = settings.YOOKASSA_SECRET_KEY

        if not all([self.yookassa_shop_id, self.yookassa_secret_key]):
            logger.warning("YooKassa credentials not configured!")

    async def create_yookassa_payment(
        self, payment: PaymentRequest
    ) -> PaymentResponse:
        if not all([self.yookassa_shop_id, self.yookassa_secret_key]):
            raise HTTPException(
                status_code=503,
                detail="Payment service not configured"
            )

        headers = {"Content-Type": "application/json"}
        auth = (self.yookassa_shop_id, self.yookassa_secret_key)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.yookassa_url,
                    json={
                        "amount": {
                            "value": str(payment.amount),
                            "currency": payment.currency,
                        },
                        "confirmation": {
                            "type": "redirect",
                            "return_url": (
                                "http://localhost:3000/payment-success"
                            ),
                        },
                        "description": payment.description,
                    },
                    headers=headers,
                    auth=auth,
                    timeout=10.0
                )

                if response.status_code != 200:
                    logger.error(f"YooKassa error: {response.text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="Payment service error"
                    )

                payment_data = response.json()
                confirmation_url = (
                    payment_data["confirmation"]["confirmation_url"]
                )
                return PaymentResponse(
                    payment_url=confirmation_url,
                    status=payment_data["status"],
                    payment_id=payment_data["id"]
                )

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Payment service timeout"
            )
        except Exception as e:
            logger.exception("Payment service error")
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )
