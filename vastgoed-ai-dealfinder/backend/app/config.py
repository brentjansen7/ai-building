from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://vastgoed_user:password@localhost:5432/vastgoed_ai",
        alias="DATABASE_URL"
    )
    database_url_sync: str = Field(
        default="postgresql://vastgoed_user:password@localhost:5432/vastgoed_ai",
        alias="DATABASE_URL_SYNC"
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # AI APIs
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")

    # Notifications
    telegram_token: str = Field(default="", alias="TELEGRAM_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")
    discord_webhook_url: str = Field(default="", alias="DISCORD_WEBHOOK_URL")
    alert_email: str = Field(default="", alias="ALERT_EMAIL")
    smtp_host: str = Field(default="smtp.gmail.com", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_pass: str = Field(default="", alias="SMTP_PASS")

    # Extension API
    extension_api_key: str = Field(default="dev_key_change_in_prod", alias="EXTENSION_API_KEY")
    api_secret_key: str = Field(default="dev_secret_change_in_prod", alias="API_SECRET_KEY")

    # Alert thresholds
    min_deal_score: int = Field(default=70, alias="MIN_DEAL_SCORE")
    min_roi_percentage: float = Field(default=15.0, alias="MIN_ROI_PERCENTAGE")
    min_profit: int = Field(default=30000, alias="MIN_PROFIT")
    alert_grades: str = Field(default="A,B", alias="ALERT_GRADES")

    # Proxies
    proxy_list: str = Field(default="", alias="PROXY_LIST")

    # Environment
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def proxy_list_parsed(self) -> List[str]:
        if not self.proxy_list:
            return []
        return [p.strip() for p in self.proxy_list.split(",") if p.strip()]

    @property
    def alert_grades_list(self) -> List[str]:
        return [g.strip() for g in self.alert_grades.split(",")]

    class Config:
        env_file = ".env"
        populate_by_name = True


settings = Settings()
