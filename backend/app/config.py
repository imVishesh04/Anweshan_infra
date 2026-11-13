from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Required settings (no defaults in code)
    MONGO_URL: str
    DB_NAME: str
    JWT_SECRET: str
    ADMIN_PASSWORD: str

    # Optional settings
    ADMIN_EMAIL: str = "admin@anweshaninfra.com"
    ENV: str = "dev"
    CORS_ORIGINS: str = "http://localhost:3000"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"

    # Storage settings
    STORAGE_BACKEND: str = "local"
    UPLOAD_DIR: str = "backend/uploads"
    R2_ACCOUNT_ID: str | None = None
    R2_ACCESS_KEY_ID: str | None = None
    R2_SECRET_ACCESS_KEY: str | None = None
    R2_BUCKET: str | None = None

    # Lead notification settings
    NOTIFY_TELEGRAM_BOT_TOKEN: str | None = None
    NOTIFY_TELEGRAM_CHAT_ID: str | None = None
    RESEND_API_KEY: str | None = None
    NOTIFY_EMAIL_TO: str | None = None
    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    TWILIO_WHATSAPP_FROM: str | None = None
    OWNER_WHATSAPP: str | None = None
    NOTIFY_EMAIL_FROM: str = "ANWESHAN Infra <onboarding@resend.dev>"

    # Shared secret for Netlify's signed proxy (netlify.toml `signed = "NETLIFY_PROXY_SECRET"`).
    # When set, the real visitor IP is taken from Netlify's signed headers.
    NETLIFY_PROXY_SECRET: str | None = None

    # WhatsApp Cloud API bot (all four must be set for the bot to run)
    WA_VERIFY_TOKEN: str | None = None  # any long random text; the same text goes in Meta's webhook setup
    WA_APP_SECRET: str | None = None  # Meta app > App settings > Basic > App secret
    WA_ACCESS_TOKEN: str | None = None  # permanent System User token
    WA_PHONE_NUMBER_ID: str | None = None  # WhatsApp > API setup > Phone number ID
    WA_GRAPH_VERSION: str = "v25.0"
    # Number customers can call / WhatsApp to talk to a person (shown at the end of the chat)
    WA_OWNER_CONTACT: str | None = None

    @property
    def whatsapp_enabled(self) -> bool:
        return bool(
            self.WA_VERIFY_TOKEN and self.WA_APP_SECRET and self.WA_ACCESS_TOKEN and self.WA_PHONE_NUMBER_ID
        )

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if not v or len(v.strip()) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long.")
        return v.strip()

    @property
    def cors_origins_list(self) -> list[str]:
        origins = [
            o.strip()
            for o in self.CORS_ORIGINS.split(",")
            if o.strip() and o.strip() != "*"
        ]
        return origins or ["http://localhost:3000"]

    @property
    def resolved_upload_dir(self) -> Path:
        p = Path(self.UPLOAD_DIR)
        if not p.is_absolute():
            # Resolve relative to project root (parent of backend) or backend
            p = (BACKEND_DIR.parent / p).resolve()
        return p


@lru_cache
def get_settings() -> Settings:
    return Settings()
