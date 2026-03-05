"""Application settings."""

from dataclasses import dataclass
from os import getenv


def _parse_csv(value: str) -> list[str]:
    """Parse comma-separated environment value."""
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment."""

    app_name: str = getenv("APP_NAME", "MyRoute API")
    app_version: str = getenv("APP_VERSION", "0.1.0")
    api_prefix: str = getenv("API_PREFIX", "/api/v1")
    database_url: str = getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/postgres",
    )
    jwt_secret_key: str = getenv(
        "JWT_SECRET_KEY",
        "change-me-in-env-change-me-in-env-12345",
    )
    jwt_algorithm: str = getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    frontend_base_url: str = getenv("FRONTEND_BASE_URL", "http://localhost:5173")
    cors_origins: tuple[str, ...] = tuple(
        _parse_csv(getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"))
    )


settings = Settings()
