from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SV_")

    app_name: str = "StockView India API"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/stockview"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me"
    access_token_minutes: int = 15
    refresh_token_days: int = 7


settings = Settings()