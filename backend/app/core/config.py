"""Application configuration loaded from environment variables."""

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Explicitly load .env from project root before Settings is defined
from dotenv import load_dotenv

# Find project root (3 levels up from this file: app/core/config.py -> backend/)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)


class Settings(BaseSettings):
    """Central application settings.

    Values are read from environment variables or a local .env file.
    """

    # Load environment variables from the **project root** .env file.
    # Previously this pointed to a .env located next to the settings module,
    # which caused duplicate configuration files in `backend/.env` and
    # `frontend/.env`. By using a relative path that climbs to the repository
    # root we ensure a single source of truth.
    model_config = SettingsConfigDict(
        env_file="../../../.env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application – values should be provided via the root .env.
    # Example env vars: ENVIRONMENT, PROJECT_NAME, API_V1_PREFIX
    environment: str | None = None
    project_name: str | None = None
    api_v1_prefix: str | None = None

    # Database – connection string supplied via .env (DATABASE_URL).
    database_url: str | None = None

    # Security – secrets must be supplied via environment variables. The
    # placeholders are kept only for type hinting; they are considered insecure
    # and will trigger validation unless the ``ALLOW_INSECURE`` flag is set.
    jwt_secret: str | None = None
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    aes_master_key: str | None = None

    # Password reset token lifetime (minutes)
    password_reset_expire_minutes: int = 30

    # Initial admin credentials – should be supplied via environment variables
    # and not hard‑coded. These values are used by the seeding process to create
    # the first admin user. In production they are considered sensitive and must
    # be stored in the root ``.env`` file.
    # Example env vars: INITIAL_ADMIN_EMAIL, INITIAL_ADMIN_PASSWORD,
    # INITIAL_ADMIN_FIRST_NAME, INITIAL_ADMIN_LAST_NAME
    initial_admin_email: str | None = None
    initial_admin_password: str | None = None
    initial_admin_first_name: str | None = None
    initial_admin_last_name: str | None = None

    # Object storage (MinIO) – values should be supplied via the root .env.
    # In production these are sensitive credentials and must not be hard‑coded.
    # Example env vars: MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY,
    # MINIO_BUCKET, MINIO_SECURE
    minio_endpoint: str | None = None
    minio_access_key: str | None = None
    minio_secret_key: str | None = None
    minio_bucket: str | None = None
    minio_secure: bool = False

    # File upload limits
    max_upload_bytes: int = 25 * 1024 * 1024
    allowed_upload_types: str = "application/pdf,image/png,image/jpeg,application/dicom,text/plain"

    @property
    def allowed_upload_types_set(self) -> set[str]:
        return {item.strip() for item in self.allowed_upload_types.split(",") if item.strip()}

    # CORS – comma‑separated list of allowed origins (CORS_ORIGINS).
    cors_origins: str | None = None

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    # Phase 4: Institutional Keys for envelope encryption – must be provided
    # via environment variables. They are optional at type level but required
    # for production use; validation will enforce presence unless insecure mode
    # is explicitly allowed.
    institutional_public_key: str | None = None
    institutional_private_key: str | None = None

    # Development flag to allow insecure defaults (useful for quick local
    # startup). Set ``ALLOW_INSECURE=true`` in the environment to bypass the
    # strict validation.
    allow_insecure: bool = False

    # ---------------------------------------------------------------------
    # Validation
    # ---------------------------------------------------------------------
    # Ensure that insecure placeholder defaults are not used in production.
    # Pydantic v2 provides a ``model_validator`` hook that runs after model
    # creation. We use it to raise an error if any placeholder values are
    # present.
    from pydantic import model_validator

    @model_validator(mode='before')
    def _ensure_secure_defaults(cls, values: dict) -> dict:  # type: ignore[override]
        """Validate that required secrets are present and have sufficient entropy.

        * ``jwt_secret`` – at least 32 characters.
        * ``aes_master_key`` – base64‑encoded 32‑byte key (>=44 chars).
        * ``institutional_public_key`` / ``institutional_private_key`` – non‑placeholder base64 strings.
        The ``ALLOW_INSECURE`` flag bypasses these checks for local development.
        """
        if values.get("allow_insecure"):
            return values

        insecure = []
        # JWT secret must be a high‑entropy string (>=32 chars)
        jwt_secret = values.get("jwt_secret")
        if not jwt_secret or len(jwt_secret) < 32:
            insecure.append("jwt_secret (must be >=32 chars)")

        # AES master key must be a base64‑encoded 32‑byte key (44+ chars)
        aes_key = values.get("aes_master_key")
        if not aes_key or len(aes_key) < 44:
            insecure.append("aes_master_key (must be base64 32‑byte key)")

        # Institutional keys must be provided and not the placeholder value
        if not values.get("institutional_public_key") or values.get("institutional_public_key").startswith("change_me"):
            insecure.append("institutional_public_key")
        if not values.get("institutional_private_key") or values.get("institutional_private_key").startswith("change_me"):
            insecure.append("institutional_private_key")

        # MinIO credentials must be provided in production.
        if not values.get("minio_endpoint"):
            insecure.append("minio_endpoint")
        if not values.get("minio_access_key"):
            insecure.append("minio_access_key")
        if not values.get("minio_secret_key"):
            insecure.append("minio_secret_key")
        if not values.get("minio_bucket"):
            insecure.append("minio_bucket")

        # Application settings – required for proper operation.
        if not values.get("environment"):
            insecure.append("environment")
        if not values.get("project_name"):
            insecure.append("project_name")
        if not values.get("api_v1_prefix"):
            insecure.append("api_v1_prefix")

        # Database URL must be supplied.
        if not values.get("database_url"):
            insecure.append("database_url")

        # CORS origins list should be defined (even if empty is allowed).
        if values.get("cors_origins") is None:
            insecure.append("cors_origins")

        if insecure:
            raise RuntimeError(
                f"Missing or insecure configuration for: {', '.join(insecure)}. "
                "Set proper high‑entropy environment variables before starting the application "
                "or enable ALLOW_INSECURE for development."
            )
        return values


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
