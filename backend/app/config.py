from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    database_url: str = "sqlite:///./campaignpulse.db"
    openai_api_key: str = ""
    meta_ads_access_token: str = ""
    meta_ads_ad_account_id: str = ""
    google_ads_developer_token: str = ""
    google_ads_client_id: str = ""
    google_ads_client_secret: str = ""
    google_ads_refresh_token: str = ""
    google_ads_login_customer_id: str = ""
    host: str = "0.0.0.0"
    port: int = 8000
    api_key: str = ""
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    log_level: str = "INFO"

    # Security: CORS hardening
    # IMPORTANT: In production, cors_origins must be set to specific origins
    # (comma-separated), NOT "*". Wildcard CORS disallows credentials and
    # opens the API to cross-origin requests from any site. The default
    # above restricts to local development origins — adjust for deployment.

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
