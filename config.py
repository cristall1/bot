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

    @property
    def admin_ids_list(self) -> List[int]:
        if not self.admin_ids:
            return []
        return [int(id.strip()) for id in self.admin_ids.split(",") if id.strip()]


settings = Settings()
