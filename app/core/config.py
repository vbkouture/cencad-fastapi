"""Application configuration.

Settings loaded from environment variables with defaults.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # JWT settings
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # MongoDB settings
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db: str = "appdb"
    mongodb_username: str | None = None
    mongodb_password: str | None = None

    # App settings
    debug: bool = False


settings = Settings()
