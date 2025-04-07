import secrets
from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Rockwell"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Environment settings
    DEBUG: bool = False
    SHOW_DOCS: bool = True
    AUTO_CREATE_TABLES: bool = False
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "rockwell"
    DATABASE_URL: Optional[PostgresDsn] = None

    # Twitter API
    TWITTER_API_KEY: str = ""
    TWITTER_API_SECRET: str = ""
    TWITTER_ACCESS_TOKEN: str = ""
    TWITTER_ACCESS_SECRET: str = ""
    
    # Qualtrics integration
    QUALTRICS_API_TOKEN: str = ""
    QUALTRICS_BASE_URL: str = ""
    
    # ML model settings
    RECSYS_MODEL_PATH: str = "models/recommender.pkl"
    RECSYS_RETRAIN_INTERVAL: int = 24  # hours
    
    @field_validator("DATABASE_URL", mode="after")
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if v:
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"{values.get('POSTGRES_DB') or ''}",
        )
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()