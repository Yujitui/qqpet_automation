from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/qqpet"
    
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_NAME: Optional[str] = None
    
    JWT_SECRET_KEY: str = "your-secret-key-change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"
    
    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


settings = Settings()

SQLITE_DATABASE_URL = "sqlite:///./qqpet.db"
