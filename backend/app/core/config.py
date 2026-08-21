from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SV_")

    app_name: str = "StockView India API"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # SQLite for zero-infra dev; point at Postgres for prod:
    # postgresql+asyncpg://user:pass@localhost:5432/stockview
    database_url: str = "sqlite+aiosqlite:///./stockview.db"
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    cookie_secure: bool = False
    cookie_domain: str | None = None
    cors_origins: list[str] = ["http://localhost:3000"]

    # Security
    login_rate_limit_per_minute: int = 5

    # Seeded users (parity with legacy app.py USERS map)
    seed_users: dict[str, str] = {"demo": "demo123", "admin": "admin123"}


settings = Settings()