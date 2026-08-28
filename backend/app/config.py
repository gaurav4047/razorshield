from decimal import Decimal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/revenue_recovery"
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    GOOGLE_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    APP_BASE_URL: str = "http://localhost:8000"

    # RBI bank rate per MSMED Act Section 16 (verified 5.50% as of August 2026; re-check at rbi.org.in)
    RBI_BANK_RATE: Decimal = Decimal("5.50")

    # Module C config
    ABANDONED_ORDER_THRESHOLD_MINUTES: int = 30
    LOW_VALUE_FLOOR_PAISE: int = 20000  # Rs 200

    # Confidence threshold
    AI_CONFIDENCE_THRESHOLD: float = 0.6


settings = Settings()
