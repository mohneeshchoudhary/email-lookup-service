from pydantic_settings import BaseSettings
from pydantic import AnyUrl, Field
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "Email Lookup Service"
    APP_ENV: str = "dev"
    LOG_LEVEL: str = "INFO"
    PORT: int = 8080
    ALLOWED_ORIGINS: str = "*"  # comma separated

    DATABASE_URL: str = "sqlite+aiosqlite:///./data/app.db"

    REDIS_URL: Optional[str] = None

    RATE_LIMIT_PER_MINUTE: int = 60
    CACHE_TTL_SECONDS: int = 60 * 60 * 12  # 12h

    GITHUB_API_BASE: str = "https://api.github.com"
    GITHUB_TOKEN: Optional[str] = None
    HUGGINGFACE_BASE: str = "https://huggingface.co"
    HUGGINGFACE_TOKEN: Optional[str] = None

    PROMETHEUS_ENABLED: bool = True

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

settings = Settings()
