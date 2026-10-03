from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SV_")

    app_name: str = "StockView India API"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # PostgreSQL everywhere (local dev runs in Docker — see docker-compose.yml):
    # postgresql+asyncpg://postgres:postgres@localhost:5432/stockview
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/stockview"
    redis_url: str = "redis://localhost:6379/0"

    # Second, isolated database holding ONLY scraped news articles. News is the
    # bulkiest and fastest-growing data we store, so it gets its own budget
    # rather than competing with user/app rows in `database_url`.
    # Neon bills storage per *project*, so pointing this at a second project is
    # what actually buys a separate allowance (a second database inside one
    # project would share the same 0.5 GB).
    # Accepts SV_DATABASE_NEWS_URL (canonical) or SV_NEWS_DB_URL.
    news_db_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/stockview_news",
        validation_alias=AliasChoices("SV_DATABASE_NEWS_URL", "SV_NEWS_DB_URL"),
    )

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

    # Blockchain
    blockchain_rpc_url: str = "http://127.0.0.1:7545"
    blockchain_contract_address: str = ""


settings = Settings()