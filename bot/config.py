from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Telegram
    BOT_TOKEN: str

    # OpenAI / ChatGPT
    OPENAI_API_KEY: str

    # Anthropic / Claude
    ANTHROPIC_API_KEY: str
    ANTHROPIC_BASE_URL: Optional[str] = None

    # Deepseek
    DEEPSEEK_API_KEY: str

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./neur_ai.db"

    @field_validator("DATABASE_URL")
    def adjust_database_url(cls, v: str) -> str:
        if v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # Admin
    ADMIN_IDS: str = ""
    ADMIN_USERNAME: str = "admin"  # without @

    # Bot settings
    BOT_NAME: str = "NEUR AI"

    @property
    def admin_list(self) -> list[int]:
        if not self.ADMIN_IDS:
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip()]

    class Config:
        env_file = (".env", "../.env")
        extra = "ignore"


settings = Settings()
