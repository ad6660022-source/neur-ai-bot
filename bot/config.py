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

    # Admin
    ADMIN_IDS: str = ""

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
