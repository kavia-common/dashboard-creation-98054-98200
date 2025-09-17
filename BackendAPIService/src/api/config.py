import os
from functools import lru_cache
from typing import List, Optional

from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

# Load env vars from .env if present
load_dotenv()


class Settings(BaseModel):
    """Application settings loaded from environment variables for secure configuration."""
    APP_NAME: str = Field(default="Dashboard Backend API", description="FastAPI application title")
    APP_DESC: str = Field(
        default="Secure REST API for authentication, users, reports, and charts",
        description="FastAPI application description",
    )
    APP_VERSION: str = Field(default="1.0.0", description="API version")
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: ["*"], description="Allowed CORS origins"
    )
    # NOTE: In production, JWT_SECRET_KEY MUST be provided via environment.
    # For container startup robustness in non-prod, we allow a development default.
    JWT_SECRET_KEY: str = Field(default="CHANGE_ME_DEV_SECRET_NOT_FOR_PROD", description="Secret key for JWT signing")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24, description="Access token expiry in minutes")

    # Demo credentials - in a real system this comes from DB
    DEMO_ADMIN_EMAIL: str = Field(default="admin@example.com", description="Seed admin email for demo")
    DEMO_ADMIN_PASSWORD_HASH: Optional[str] = Field(
        default=None, description="BCrypt hash of seed admin password for demo"
    )

    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = Field(default=10, description="Default pagination size")


@lru_cache
def get_settings() -> Settings:
    """Load settings from environment variables, with validation."""
    try:
        # Read raw envs
        cors = os.getenv("CORS_ORIGINS", "*")
        origins = [o.strip() for o in cors.split(",")] if cors else ["*"]
        data = {
            "APP_NAME": os.getenv("APP_NAME", "Dashboard Backend API"),
            "APP_DESC": os.getenv(
                "APP_DESC",
                "Secure REST API for authentication, users, reports, and charts",
            ),
            "APP_VERSION": os.getenv("APP_VERSION", "1.0.0"),
            "CORS_ORIGINS": origins,
            "JWT_SECRET_KEY": os.getenv("JWT_SECRET_KEY"),
            "JWT_ALGORITHM": os.getenv("JWT_ALGORITHM", "HS256"),
            "ACCESS_TOKEN_EXPIRE_MINUTES": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")),
            "DEMO_ADMIN_EMAIL": os.getenv("DEMO_ADMIN_EMAIL", "admin@example.com"),
            "DEMO_ADMIN_PASSWORD_HASH": os.getenv("DEMO_ADMIN_PASSWORD_HASH"),
            "DEFAULT_PAGE_SIZE": int(os.getenv("DEFAULT_PAGE_SIZE", "10")),
        }
        return Settings(**data)
    except (ValidationError, ValueError) as e:
        # Fail fast with clear message
        raise RuntimeError(f"Invalid configuration: {e}") from e
