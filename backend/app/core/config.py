"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings.

    Values are read from environment variables or a local .env file.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    environment: str = "development"
    project_name: str = "Voda EHRs"
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+psycopg://voda:postgres@localhost:5432/voda_ehrs"

    # Security
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    aes_master_key: str = "base64_32_byte_key"

    # Password reset token lifetime (minutes)
    password_reset_expire_minutes: int = 30

    # Initial admin seeded on first migration/seed run.
    # Note: email-validator rejects reserved TLDs like .local, so use a real domain.
    initial_admin_email: str = "admin@vodaehrs.com"
    initial_admin_password: str = "password"
    initial_admin_first_name: str = "Voda"
    initial_admin_last_name: str = "Admin"

    # Object storage
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket: str = "voda-records"
    minio_secure: bool = False

    # CORS: comma-separated list of allowed origins
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
