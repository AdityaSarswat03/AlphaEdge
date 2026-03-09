"""
Configuration Management for AlphaEdge
"""

from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    # ── Application ──────────────────────────────────────────────
    app_name: str = "AlphaEdge"
    app_env: str = "development"
    debug: bool = True
    # OWASP: No usable default in production.  The model_post_init
    # guard below will refuse to start if this is left as the default.
    secret_key: str = Field(default="dev-secret-key-change-in-production")

    # ── API ──────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    api_reload: bool = True

    # ── Dashboard ────────────────────────────────────────────────
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8501

    # ── Firebase (Database & Backend) ────────────────────────────
    firebase_project_id: str = ""
    firebase_credentials_path: str = ""  # path to service-account JSON
    firebase_credentials_json: str = Field(default="", repr=False)  # repr=False: hide from logs
    firebase_storage_bucket: str = ""  # e.g. "alphaedge-xxxxx.appspot.com"
    firebase_database_url: str = ""  # Realtime DB (optional)

    # ── Clerk (Authentication) ───────────────────────────────────
    clerk_publishable_key: str = ""  # pk_live_… or pk_test_…
    clerk_secret_key: str = Field(default="", repr=False)  # OWASP: never log secrets
    clerk_domain: str = ""  # e.g. "your-app.clerk.accounts.dev"
    enable_clerk_auth: bool = False  # toggle off for local dev

    # ── Cloudflare (DNS & CDN) ───────────────────────────────────
    cloudflare_api_token: str = Field(default="", repr=False)
    cloudflare_zone_id: str = ""
    cloudflare_account_id: str = ""
    domain_name: str = "alphaedge.ai"  # your Cloudflare-managed domain
    api_subdomain: str = "api"  # api.alphaedge.ai
    dashboard_subdomain: str = "app"  # app.alphaedge.ai

    # ── Redis (optional cache) ───────────────────────────────────
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = Field(default="", repr=False)

    # ── Paths ────────────────────────────────────────────────────
    base_dir: Path = Path(__file__).resolve().parent.parent.parent.parent
    data_dir: Optional[Path] = Field(default=None)
    model_dir: Optional[Path] = Field(default=None)
    log_dir: Optional[Path] = Field(default=None)
    cache_dir: Optional[Path] = Field(default=None)

    def model_post_init(self, __context):
        """Compute derived paths and apply production lockdowns."""
        if self.data_dir is None:
            self.data_dir = self.base_dir / "data"
        if self.model_dir is None:
            self.model_dir = self.base_dir / "models"
        if self.log_dir is None:
            self.log_dir = self.base_dir / "logs"
        if self.cache_dir is None:
            self.cache_dir = self.base_dir / ".cache"

        # Production lockdowns
        if self.app_env == "production":
            self.debug = False
            self.api_reload = False
            # OWASP: Refuse to start with the default dev secret key.
            if self.secret_key == "dev-secret-key-change-in-production":
                raise ValueError(
                    "SECRET_KEY must be changed from default before running in production. "
                    "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
                )

    # ── Model Configuration ──────────────────────────────────────
    max_sequence_length: int = 60
    prediction_horizon: int = 5

    # ── Training ─────────────────────────────────────────────────
    train_batch_size: int = 64
    val_batch_size: int = 128
    epochs: int = 100
    learning_rate: float = 0.001
    early_stopping_patience: int = 10

    # ── Backtesting ──────────────────────────────────────────────
    initial_capital: float = 100_000.0
    commission_rate: float = 0.001
    slippage_rate: float = 0.0005
    max_positions: int = 10

    # ── Logging ──────────────────────────────────────────────────
    log_level: str = "INFO"
    log_file: str = "logs/alphaedge.log"
    log_rotation: str = "1 day"
    log_retention: str = "30 days"

    # ── CORS / Security ──────────────────────────────────────────
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8501",
        "https://app.alphaedge.ai",
        "https://alphaedge.ai",
    ]
    rate_limit_per_minute: int = 60
    trusted_hosts: List[str] = []  # e.g. ["alphaedge.ai", "*.alphaedge.ai"]

    # ── Feature Flags ────────────────────────────────────────────
    enable_sentiment_analysis: bool = True
    enable_technical_analysis: bool = True
    enable_ensemble_model: bool = True
    enable_backtesting: bool = True
    enable_real_time_data: bool = False

    # ── Cache ────────────────────────────────────────────────────
    cache_ttl_seconds: int = 300
    enable_redis_cache: bool = False  # default off for local dev

    # ── API Keys (optional) ──────────────────────────────────────
    # OWASP: All keys loaded from env vars, never hard-coded.
    # repr=False prevents accidental logging of secrets.
    yahoo_finance_api_key: str = Field(default="", repr=False)
    alpha_vantage_api_key: str = Field(default="", repr=False)
    news_api_key: str = Field(default="", repr=False)

    # ── GitHub ───────────────────────────────────────────────────
    github_repo: str = "adityas/AlphaEdge"  # owner/repo
    github_token: str = Field(default="", repr=False)

    class Config:
        env_file = ".env"
        case_sensitive = False


# ── Global singleton ─────────────────────────────────────────────
settings = Settings()

# Ensure directories exist
for d in (settings.data_dir, settings.model_dir, settings.log_dir, settings.cache_dir):
    d.mkdir(parents=True, exist_ok=True)
