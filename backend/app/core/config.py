"""
Application configuration using Pydantic Settings
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""

    # Project
    PROJECT_NAME: str = "AI Trading System"
    VERSION: str = "0.2.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")

    # Server
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    RELOAD: bool = Field(default=True, env="RELOAD")
    DEBUG: bool = Field(default=True, env="DEBUG")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://trading_user:trading_pass@localhost:5432/trading_db",
        env="DATABASE_URL"
    )

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )

    # Security
    SECRET_KEY: str = Field(
        default="change-me-in-production-min-32-chars-long-secret-key",
        env="SECRET_KEY"
    )
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="ALLOWED_ORIGINS"
    )

    # Telegram
    TELEGRAM_BOT_TOKEN: str = Field(default="", env="TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: str = Field(default="", env="TELEGRAM_CHAT_ID")

    # Discord
    DISCORD_WEBHOOK_URL: str = Field(default="", env="DISCORD_WEBHOOK_URL")

    # Twilio (SMS)
    TWILIO_ACCOUNT_SID: str = Field(default="", env="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = Field(default="", env="TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: str = Field(default="", env="TWILIO_PHONE_NUMBER")
    RECIPIENT_PHONE_NUMBER: str = Field(default="", env="RECIPIENT_PHONE_NUMBER")

    # Market Data
    CCXT_EXCHANGE: str = Field(default="binance", env="CCXT_EXCHANGE")
    CCXT_API_KEY: str = Field(default="", env="CCXT_API_KEY")
    CCXT_API_SECRET: str = Field(default="", env="CCXT_API_SECRET")

    # Analysis Settings
    ANALYSIS_INTERVAL_MINUTES: int = Field(default=5, env="ANALYSIS_INTERVAL_MINUTES")
    DEFAULT_TIMEFRAMES: str = Field(default="M5,M15,H1,H4,D1", env="DEFAULT_TIMEFRAMES")
    DEFAULT_SYMBOLS: str = Field(default="DAX,SPX500,EURUSD,BTCUSD", env="DEFAULT_SYMBOLS")

    # Alert Settings
    ALERT_COOLDOWN_MINUTES: int = Field(default=15, env="ALERT_COOLDOWN_MINUTES")
    ALERT_MAX_PER_HOUR: int = Field(default=10, env="ALERT_MAX_PER_HOUR")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE_PATH: str = Field(default="./logs/app.log", env="LOG_FILE_PATH")

    # LLM
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    OLLAMA_MODEL: str = Field(default="mistral:7b", env="OLLAMA_MODEL")

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
