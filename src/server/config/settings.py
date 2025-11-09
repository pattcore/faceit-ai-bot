try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings

from pydantic import validator
from functools import lru_cache
import os
from typing import List, Optional

class Settings(BaseSettings):
    # App settings
    APP_TITLE: str = "Faceit AI Bot Service"
    APP_VERSION: str = "0.2.2"
    NODE_ENV: str = "production"
    REPLIT_DEV_DOMAIN: Optional[str] = None
    
    # Database settings
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/faceit_ai_bot"
    
    # Faceit API settings
    FACEIT_API_KEY: Optional[str] = None
    
    # AI Services
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    HUGGINGFACE_TOKEN: Optional[str] = None
    
    # Security settings
    SECRET_KEY: str = "change-me-in-production-min-32-characters-long"
    ALGORITHM: str = "HS256"
    
    # Payment settings
    WEBSITE_URL: str = "http://localhost:3000"
    API_URL: str = "http://localhost:8000"
    
    @validator('DATABASE_URL')
    def validate_database_url(cls, v):
        if not v.startswith(('postgresql://', 'postgresql+asyncpg://', 'sqlite://')):
            raise ValueError('Invalid database URL. Must start with postgresql://, postgresql+asyncpg://, or sqlite://')
        return v
    
    @validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters long for security')
        return v
    
    # СБП API settings
    SBP_TINKOFF_API_URL: str = "https://securepay.tinkoff.ru/v2"
    SBP_TINKOFF_TOKEN: Optional[str] = None
    SBP_TINKOFF_TERMINAL_KEY: Optional[str] = None
    
    SBP_SBERBANK_API_URL: str = "https://api.sberbank.ru/qr"
    SBP_SBERBANK_TOKEN: Optional[str] = None
    
    SBP_VTB_API_URL: str = "https://api.vtb.ru/qr"
    SBP_VTB_TOKEN: Optional[str] = None
    
    SBP_ALPHA_API_URL: str = "https://alfabank.ru/api"
    SBP_ALPHA_TOKEN: Optional[str] = None
    
    # Stripe settings (для международных карт)
    STRIPE_API_URL: str = "https://api.stripe.com"
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    
    # Crypto settings (Binance API)
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_SECRET_KEY: Optional[str] = None
    
    # PayPal settings (для нероссийских платежей)
    PAYPAL_API_URL: str = "https://api.paypal.com"
    PAYPAL_CLIENT_ID: Optional[str] = None
    PAYPAL_SECRET_KEY: Optional[str] = None
    
    # Crypto settings
    CRYPTO_API_URL: str = "https://api.crypto.com"
    CRYPTO_API_KEY: Optional[str] = None
    CRYPTO_SECRET_KEY: Optional[str] = None

    # CORS settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    # Payment settings
    YOOKASSA_API_URL: str = "https://api.yookassa.ru/v3/payments"
    YOOKASSA_SHOP_ID: Optional[str] = None
    YOOKASSA_SECRET_KEY: Optional[str] = None

    # SBP settings
    SBP_API_URL: Optional[str] = None
    SBP_TOKEN: Optional[str] = None

    # Redis settings (для кэширования)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    
    # Test settings
    TEST_ENV: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()