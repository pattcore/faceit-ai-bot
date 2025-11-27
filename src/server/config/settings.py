from pathlib import Path
from dotenv import load_dotenv
from functools import lru_cache
from typing import List, Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings

from pydantic import validator

# Load environment variables from .env
env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    # App settings
    APP_TITLE: str = "Faceit AI Bot Service"
    APP_VERSION: str = "0.4.0"
    NODE_ENV: str = "production"
    REPLIT_DEV_DOMAIN: Optional[str] = None

    # Database settings
    DATABASE_URL: str = (
        "postgresql://user:password@localhost:5432/faceit_ai_bot"
    )

    # Faceit API & OAuth settings
    FACEIT_API_KEY: Optional[str] = None
    FACEIT_CLIENT_ID: Optional[str] = None
    FACEIT_CLIENT_SECRET: Optional[str] = None

    # Steam Web API settings
    STEAM_WEB_API_KEY: Optional[str] = None

    # AI Services
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    HUGGINGFACE_TOKEN: Optional[str] = None

    LOCAL_LLM_BASE_URL: Optional[str] = None
    LOCAL_LLM_MODEL: Optional[str] = None
    LOCAL_LLM_API_KEY: Optional[str] = None

    # Security settings
    SECRET_KEY: str = "change-me-in-production-min-32-characters-long"
    ALGORITHM: str = "HS256"

    # CAPTCHA settings (e.g. Cloudflare Turnstile)
    CAPTCHA_PROVIDER: Optional[str] = None
    TURNSTILE_SITE_KEY: Optional[str] = None
    TURNSTILE_SECRET_KEY: Optional[str] = None

    # Yandex SmartCaptcha settings
    SMARTCAPTCHA_SITE_KEY: Optional[str] = None
    SMARTCAPTCHA_SECRET_KEY: Optional[str] = None

    # Rate limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_REQUESTS_PER_HOUR: int = 1000
    RATE_LIMIT_BAN_ENABLED: bool = False
    RATE_LIMIT_BAN_THRESHOLD: int = 20
    RATE_LIMIT_BAN_WINDOW_SECONDS: int = 600
    RATE_LIMIT_BAN_TTL_SECONDS: int = 3600
    RATE_LIMIT_BYPASS_USER_ID: Optional[int] = None

    # Payment settings
    WEBSITE_URL: str = "http://localhost:3000"
    API_URL: str = "http://localhost:8000"

    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        allowed_prefixes = (
            "postgresql://",
            "postgresql+asyncpg://",
            "sqlite://",
        )
        if not v.startswith(allowed_prefixes):
            raise ValueError(
                "Invalid database URL. Must start with postgresql://, "
                "postgresql+asyncpg://, or sqlite://"
            )
        return v

    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long for security"
            )
        return v

    # SBP API settings
    SBP_TINKOFF_API_URL: str = "https://securepay.tinkoff.ru/v2"
    SBP_TINKOFF_TOKEN: Optional[str] = None
    SBP_TINKOFF_TERMINAL_KEY: Optional[str] = None

    SBP_SBERBANK_API_URL: str = "https://api.sberbank.ru/qr"
    SBP_SBERBANK_TOKEN: Optional[str] = None

    SBP_VTB_API_URL: str = "https://api.vtb.ru/qr"
    SBP_VTB_TOKEN: Optional[str] = None

    SBP_ALPHA_API_URL: str = "https://alfabank.ru/api"
    SBP_ALPHA_TOKEN: Optional[str] = None

    # Stripe settings (for international cards)
    STRIPE_API_URL: str = "https://api.stripe.com"
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None

    # Crypto settings (Binance API)
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_SECRET_KEY: Optional[str] = None

    # PayPal settings (for non-Russian payments)
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
        "https://pattmsc.online",
        "https://www.pattmsc.online",
    ]

    # Payment settings
    YOOKASSA_API_URL: str = "https://api.yookassa.ru/v3/payments"
    YOOKASSA_SHOP_ID: Optional[str] = None
    YOOKASSA_SECRET_KEY: Optional[str] = None

    # SBP settings
    SBP_API_URL: Optional[str] = None
    SBP_TOKEN: Optional[str] = None
    SBP_WEBHOOK_SECRET: Optional[str] = None

    # Redis settings (for caching)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None

    # Observability settings
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None
    JAEGER_HOST: str = "localhost"
    JAEGER_PORT: int = 6831
    VERSION: str = "0.4.0"

    # Directory for storing AI training samples (JSONL)
    AI_SAMPLES_DIR: str = "data"

    # Demo upload limits
    MAX_DEMO_FILE_MB: int = 100

    # Test settings
    TEST_ENV: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
