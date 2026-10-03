from pathlib import Path
from typing import List

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# backend/
BASE_DIR = Path(__file__).resolve().parents[2]

# Project root
PROJECT_ROOT = BASE_DIR.parent


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
        default=["*"],
        validation_alias="CORS_ORIGINS",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            value = value.strip()

            if value == "*":
                return ["*"]

            return [
                origin.strip()
                for origin in value.split(",")
                if origin.strip()
            ]

        return value

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