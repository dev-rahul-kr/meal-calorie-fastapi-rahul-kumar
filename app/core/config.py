from functools import lru_cache
from typing import List

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized configuration - All values come from environment variables (via .env)
    """

    # --- App meta ---
    ENV: str = Field(default="dev", description="Environment name: dev|test|prod")
    APP_NAME: str = "Meal Calorie Count API"
    LOG_LEVEL: str = Field(default="INFO", description="Python logging level (DEBUG|INFO|WARNING|ERROR)")

    # --- Database ---
    DATABASE_URL: str = Field(..., description="SQLAlchemy URL, e.g. postgresql+psycopg://user:pass@host:5432/db")

    # --- Auth / JWT ---
    JWT_SECRET: SecretStr = Field(..., description="Secret for signing JWTs")
    JWT_ALGO: str = Field(default="HS256", description="JWT signing algorithm")
    JWT_EXPIRES_MIN: int = Field(default=60, ge=5, le=24 * 60, description="Access token expiry in minutes")

    # --- Rate limiting ---
    RATE_LIMIT_PER_MIN: int = Field(default=60, ge=1, description="Default requests/min per IP")
    LOGIN_RATE_LIMIT_PER_MIN: int = Field(default=20, ge=1, description="Requests/min for /auth/login")

    # --- USDA API ---
    USDA_BASE_URL: str = Field(
        default="https://api.nal.usda.gov/fdc/v1/foods/search",
        description="USDA FoodData Central search endpoint",
    )
    USDA_API_KEY: SecretStr = Field(..., description="USDA API key")
    USDA_PAGE_SIZE: int = Field(default=25, ge=1, le=200, description="Default page size for USDA search")
    USDA_TIMEOUT_S: float = Field(default=10.0, ge=1.0, le=60.0, description="HTTP timeout seconds")
    USDA_RETRIES: int = Field(default=3, ge=0, le=10, description="Max HTTP retries for USDA")

    # --- Caching (for USDA search) ---
    CACHE_TTL_S: int = Field(default=600, ge=0, le=24 * 3600, description="TTL seconds; 0 disables caching")
    CACHE_MAXSIZE: int = Field(default=512, ge=1, le=10000, description="Max entries in cache")

    # --- Fuzzy matching ---
    FUZZ_THRESHOLD: int = Field(default=55, ge=0, le=100, description="Minimum score to accept a match")

    # --- CORS ---
    CORS_ORIGINS: str = Field(
        default="",
        description='Comma-separated origins (e.g., "http://localhost:3000,https://app.example.com")',
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="Whether to allow cookies/credentials")

    # --- Feature flags ---
    QUERY_LOG_ENABLED: bool = Field(default=False, description="Persist successful calorie queries (if model present)")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return []
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
