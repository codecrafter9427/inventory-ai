"""Application settings from environment (placeholders — see .env.example)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://inventory:inventory@localhost:5435/inventory_ai"
    jwt_secret: str = "change-me-demo-secret"
    # Demo JWT lifetime (hours). Documented in README / .env.example — not production SSO.
    jwt_access_token_hours: int = 24
    demo_mode: bool = True
    demo_admin_email: str = "admin@demo.inventory.local"
    demo_admin_password: str = "demo-password"
    # Soft password policy note for non-demo auth (demo passwords may be shorter)
    password_min_length: int = 10
    login_rate_limit_per_minute: int = 10
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"
    ai_provider: str = "demo"  # demo | ollama
    # Read-only Insights connector (Agent 5). Empty = connector auth disabled (401).
    insights_connector_token: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
