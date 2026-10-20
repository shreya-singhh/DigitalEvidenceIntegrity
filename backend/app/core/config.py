from pathlib import Path
from typing import List

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# backend/
BASE_DIR = Path(__file__).resolve().parents[2]

# Project root
PROJECT_ROOT = BASE_DIR.parent
DEPLOYED_FRONTEND_ORIGIN = "https://digital-evidence-frontend.onrender.com"


class Settings(BaseSettings):
    database_url: str = Field(..., validation_alias="DATABASE_URL")
    secret_key: str = Field(..., validation_alias="SECRET_KEY")

    jwt_algorithm: str = Field(
        default="HS256",
        validation_alias="JWT_ALGORITHM",
    )

    access_token_expire_minutes: int = Field(
        default=30,
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    upload_directory: Path = Field(
        default=PROJECT_ROOT / "uploads",
        validation_alias="UPLOAD_DIRECTORY",
    )

    report_directory: Path = Field(
        default=PROJECT_ROOT / "reports",
        validation_alias="REPORT_DIRECTORY",
    )

    debug: bool = Field(
        default=True,
        validation_alias="DEBUG",
    )

    app_name: str = Field(
        default="Digital Evidence Integrity System",
        validation_alias="APP_NAME",
    )

    app_version: str = Field(
        default="1.0.0",
        validation_alias="APP_VERSION",
    )

    cors_origins: List[str] = Field(
        default=[
            "http://localhost:5173",
            "https://digital-evidence-frontend.onrender.com",
        ],
        validation_alias="CORS_ORIGINS",
    )
    google_client_id: str | None = Field(default=None, validation_alias="GOOGLE_CLIENT_ID")
    smtp_host: str | None = Field(default=None, validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=587, ge=1, le=65535, validation_alias="SMTP_PORT")
    smtp_username: str | None = Field(default=None, validation_alias="SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, validation_alias="SMTP_PASSWORD")
    smtp_from_email: str | None = Field(default=None, validation_alias="SMTP_FROM_EMAIL")
    smtp_use_tls: bool = Field(default=True, validation_alias="SMTP_USE_TLS")
    public_app_url: str = Field(default="http://localhost:5173", validation_alias="PUBLIC_APP_URL")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            value = value.strip()

            if value == "*":
                return ["*"]

            origins = [
                origin.strip()
                for origin in value.split(",")
                if origin.strip()
            ]
        else:
            origins = list(value)

        if DEPLOYED_FRONTEND_ORIGIN not in origins:
            origins.append(DEPLOYED_FRONTEND_ORIGIN)
        return origins

    @field_validator("google_client_id", mode="before")
    @classmethod
    def normalize_google_client_id(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @property
    def google_sign_in_enabled(self) -> bool:
        value = self.google_client_id
        if value is None:
            return False
        return bool(str(value).strip())

    @property
    def email_delivery_enabled(self) -> bool:
        return bool(self.smtp_host and self.smtp_from_email)

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()

# Make sure required directories exist
settings.upload_directory.mkdir(parents=True, exist_ok=True)
settings.report_directory.mkdir(parents=True, exist_ok=True)