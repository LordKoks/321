from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@db:5432/social_api"
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str = "change-me-to-random-32-chars-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    VK_APP_ID: Optional[str] = None
    VK_APP_SECRET: Optional[str] = None
    VK_REDIRECT_URI: str = "http://localhost:8000/accounts/vk/callback"

    X_CLIENT_ID: Optional[str] = None
    X_CLIENT_SECRET: Optional[str] = None
    X_REDIRECT_URI: str = "http://localhost:8000/accounts/x/callback"

    TELEGRAM_API_ID: Optional[str] = None
    TELEGRAM_API_HASH: Optional[str] = None

    OK_APP_ID: Optional[str] = None
    OK_APP_SECRET: Optional[str] = None
    OK_PUBLIC_KEY: Optional[str] = None
    OK_REDIRECT_URI: str = "http://localhost:8000/accounts/ok/callback"

    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/accounts/youtube/callback"

    PROXY_HOST: Optional[str] = None
    PROXY_PORT: Optional[int] = None
    PROXY_USER: Optional[str] = None
    PROXY_PASSWORD: Optional[str] = None

    # Job APIs
    RAPIDAPI_KEY: Optional[str] = None          # Glassdoor via RapidAPI (100 req/mo free)
    THEIRSTACK_API_KEY: Optional[str] = None    # TheirStack (200 credits/mo free)
    SERPAPI_KEY: Optional[str] = None           # SerpApi Google Jobs (100 req/mo free)

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()


def get_settings() -> Settings:
    return settings
