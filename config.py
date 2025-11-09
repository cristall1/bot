from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    user_bot_token: str = Field(..., alias="USER_BOT_TOKEN")
    admin_bot_token: str = Field(..., alias="ADMIN_BOT_TOKEN")
    database_url: str = Field(
        default="sqlite+aiosqlite:///./bot_database.db",
        alias="DATABASE_URL"
    )
    admin_ids: str = Field(default="", alias="ADMIN_IDS")
    telegraph_token: str = Field(default="", alias="TELEGRAPH_TOKEN")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str = Field(default="bot.log", alias="LOG_FILE")
    webapp_host: str = Field(default="0.0.0.0", alias="WEBAPP_HOST")
    webapp_port: int = Field(default=8000, alias="WEBAPP_PORT")
    webapp_public_url: str = Field(default="http://localhost:8000", alias="WEBAPP_PUBLIC_URL")
    webapp_cors_origins: str = Field(default="", alias="WEBAPP_CORS_ORIGINS")
    webapp_debug_skip_auth: bool = Field(default=False, alias="WEBAPP_DEBUG_SKIP_AUTH")
    webapp_debug_user_id: int = Field(default=5912983856, alias="WEBAPP_DEBUG_USER_ID")

    @property
    def admin_ids_list(self) -> List[int]:
        if not self.admin_ids:
            return []
        return [int(id.strip()) for id in self.admin_ids.split(",") if id.strip()]

    @property
    def webapp_cors_origins_list(self) -> List[str]:
        if not self.webapp_cors_origins:
            return []
        return [origin.strip() for origin in self.webapp_cors_origins.split(",") if origin.strip()]


settings = Settings()
