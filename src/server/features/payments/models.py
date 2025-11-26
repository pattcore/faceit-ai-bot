from enum import Enum
from typing import Optional, Dict, List
from datetime import datetime
from pydantic import BaseModel


class PaymentProvider(str, Enum):
    SBP = "sbp"
    SBP_TINKOFF = "sbp_tinkoff"
    SBP_SBERBANK = "sbp_sberbank"
    SBP_VTB = "sbp_vtb"
    SBP_ALPHA = "sbp_alpha"
    YOOKASSA = "yookassa"
    QIWI = "qiwi"
    STRIPE = "stripe"
    PAYPAL = "paypal"
    CRYPTO = "crypto"


class Currency(str, Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"


class PaymentMethod(str, Enum):
    SBP = "sbp"
    BANK_CARD = "bank_card"
    QIWI_WALLET = "qiwi_wallet"
    YOOMONEY = "yoomoney"
    PAYPAL = "paypal"
    CRYPTO_BTC = "crypto_btc"
    CRYPTO_ETH = "crypto_eth"
    CRYPTO_USDT = "crypto_usdt"


class RegionPaymentMethods(BaseModel):
    region: str
    available_methods: List[PaymentMethod]
    default_currency: Currency
    enabled_providers: List[PaymentProvider]


class PriceWithCurrency(BaseModel):
    amount: float
    currency: Currency


class PaymentRequest(BaseModel):
    subscription_tier: str
    amount: float
    currency: Currency
    payment_method: PaymentMethod
    provider: PaymentProvider
    description: str = "Faceit AI Bot subscription"
    meta: Optional[Dict] = None
    captcha_token: Optional[str] = None
    user_id: Optional[str] = None


class PaymentResponse(BaseModel):
    payment_id: str
    status: str
    payment_url: str
    amount: float
    currency: Currency
    created_at: datetime
    expires_at: datetime
    confirmation_type: str  # redirect, qr, widget


class PaymentStatus(BaseModel):
    payment_id: str
    status: str
    paid: bool
    amount: float
    currency: Currency
    payment_method: PaymentMethod
    created_at: datetime
    paid_at: Optional[datetime]


# Regional payment settings
REGION_PAYMENT_CONFIG = {
    "RU": RegionPaymentMethods(
        region="RU",
        available_methods=[
            PaymentMethod.SBP,
            PaymentMethod.BANK_CARD,
            PaymentMethod.QIWI_WALLET,
            PaymentMethod.YOOMONEY,
            PaymentMethod.CRYPTO_BTC,
            PaymentMethod.CRYPTO_USDT
        ],
        default_currency=Currency.RUB,
        enabled_providers=[
            PaymentProvider.SBP,
            PaymentProvider.YOOKASSA,
            PaymentProvider.QIWI,
            PaymentProvider.CRYPTO
        ]
    ),
    "US": RegionPaymentMethods(
        region="US",
        available_methods=[
            PaymentMethod.BANK_CARD,
            PaymentMethod.PAYPAL,
            PaymentMethod.CRYPTO_BTC,
            PaymentMethod.CRYPTO_ETH,
            PaymentMethod.CRYPTO_USDT
        ],
        default_currency=Currency.USD,
        enabled_providers=[
            PaymentProvider.STRIPE,
            PaymentProvider.PAYPAL,
            PaymentProvider.CRYPTO
        ]
    ),
    "EU": RegionPaymentMethods(
        region="EU",
        available_methods=[
            PaymentMethod.BANK_CARD,
            PaymentMethod.PAYPAL,
            PaymentMethod.CRYPTO_BTC,
            PaymentMethod.CRYPTO_ETH,
            PaymentMethod.CRYPTO_USDT
        ],
        default_currency=Currency.EUR,
        enabled_providers=[
            PaymentProvider.STRIPE,
            PaymentProvider.PAYPAL,
            PaymentProvider.CRYPTO
        ]
    )
}
