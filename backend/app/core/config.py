import secrets
from typing import Any, Dict, List, Optional
from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Project Metadata
    PROJECT_NAME: str = "Rockwell"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)  # Fallback if not set in .env
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Environment Settings
    DEBUG: bool = False
    SHOW_DOCS: bool = True
    AUTO_CREATE_TABLES: bool = False

    # Remote PostgreSQL
    POSTGRES_REMOTE_HOST: Optional[str] = None
    POSTGRES_REMOTE_PORT: Optional[int] = 5432
    POSTGRES_REMOTE_DB: Optional[str] = None
    POSTGRES_REMOTE_USER: Optional[str] = None
    POSTGRES_REMOTE_PASSWORD: Optional[str] = None

    # Local PostgreSQL
    POSTGRES_LOCAL_HOST: str = "localhost"
    POSTGRES_LOCAL_PORT: int = 5432
    POSTGRES_LOCAL_DB: str = "metrics"
    POSTGRES_LOCAL_USER: str = "rockwell_manager"
    POSTGRES_LOCAL_PASSWORD: str = "infodiversity"

    # DATABASE_URL (async DSN for SQLAlchemy)
    DATABASE_URL: Optional[PostgresDsn] = None

    # Hoaxy Database
    HOAXY_DB_HOST: str = "localhost"
    HOAXY_DB_PORT: int = 5432
    HOAXY_DB_NAME: str = "hoaxy_infodiversity"
    HOAXY_DB_USER: str = "hoaxy"
    HOAXY_DB_PASSWORD: str = "hoaxy.is.for.rincewind"

    # Twitter API
    TWITTER_API_KEY: str
    TWITTER_API_SECRET: str
    TWITTER_TITLE_MAX: int = 140
    TWITTER_DESCRIPTION_MAX: int = 280

    # Web Configuration
    CALLBACK_URL: AnyHttpUrl
    QUAL_CALLBACK_URL: AnyHttpUrl
    QUAL_CALLBACK_V2: AnyHttpUrl
    APP_ROUTE: AnyHttpUrl
    APP_URL: AnyHttpUrl
    LOCALHOST_IP: str = "127.0.0.1"

    # Twitter OAuth URLs
    TWITTER_REQUEST_TOKEN_URL: AnyHttpUrl
    TWITTER_ACCESS_TOKEN_URL: AnyHttpUrl
    TWITTER_AUTHORIZE_URL: AnyHttpUrl
    TWITTER_SHOW_USER_URL: AnyHttpUrl
    TWITTER_ACCOUNT_SETTINGS_URL: AnyHttpUrl
    TWITTER_CREATION_DATE_URL: AnyHttpUrl

    @field_validator("DATABASE_URL", mode="after")
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if v:
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_LOCAL_USER"),
            password=values.get("POSTGRES_LOCAL_PASSWORD"),
            host=values.get("POSTGRES_LOCAL_HOST"),
            port=str(values.get("POSTGRES_LOCAL_PORT")),
            path=f"/{values.get('POSTGRES_LOCAL_DB') or ''}",
        )

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
