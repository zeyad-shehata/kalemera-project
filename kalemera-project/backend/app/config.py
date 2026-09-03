import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Backend project directory (app/config.py -> backend/)
BACKEND_DIR = Path(__file__).resolve().parents[1]


# Determine default base directory for storage (fallback to /tmp in Vercel/serverless environments)
IS_VERCEL = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
DEFAULT_STORAGE_BASE = Path("/tmp") if IS_VERCEL else BACKEND_DIR

# Root .env path check
ENV_FILE_PATH = os.path.join(BACKEND_DIR.parent, ".env")
if not os.path.exists(ENV_FILE_PATH):
    ENV_FILE_PATH = os.path.join(BACKEND_DIR, ".env") if os.path.exists(os.path.join(BACKEND_DIR, ".env")) else None


class Settings(BaseSettings):
    # Environment & Security
    ENVIRONMENT: str = "development"  # "development" or "production"
    DATABASE_URL: str = "sqlite+aiosqlite:///./kalemera.db"
    SECRET_KEY: str = "development_secret_key_change_in_production_32_chars_min"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    SECURE_COOKIES: bool = False

    # CORS Configuration
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:3000,http://127.0.0.1:3000"

    # Storage Directories
    STORAGE_DIR: str = str(DEFAULT_STORAGE_BASE / "storage")
    UPLOAD_DIR: str = str(DEFAULT_STORAGE_BASE / "uploads")
    PRODUCTS_IMG_DIR: str = str(DEFAULT_STORAGE_BASE / "storage" / "products")
    THUMBNAILS_IMG_DIR: str = str(DEFAULT_STORAGE_BASE / "storage" / "thumbnails")
    TEMP_DIR: str = str(DEFAULT_STORAGE_BASE / "storage" / "temp")
    BACKUPS_DIR: str = str(DEFAULT_STORAGE_BASE / "storage" / "backups")

    # Cloud Object Storage (S3 / Cloudflare R2 / Supabase / Vercel Blob)
    S3_BUCKET_NAME: str | None = None
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    S3_REGION_NAME: str | None = None
    S3_ENDPOINT_URL: str | None = None
    S3_PUBLIC_URL: str | None = None

    # Image Optimization & Limits
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB maximum incoming upload file
    IMAGE_MAX_WIDTH: int = 1200
    IMAGE_MAX_HEIGHT: int = 1200
    IMAGE_QUALITY: int = 80
    THUMBNAIL_MAX_WIDTH: int = 400
    THUMBNAIL_MAX_HEIGHT: int = 400

    # Backups & Hosting Constraints
    BACKUP_RETENTION_COUNT: int = 7
    HOSTING_STORAGE_LIMIT_BYTES: int = 10737418240  # 10 GB in bytes (10 * 1024 * 1024 * 1024)

    # Business Hours
    BUSINESS_TIMEZONE: str = "Africa/Cairo"  # Restaurant business timezone
    ENABLE_BUSINESS_HOURS: bool = True  # Master switch for order acceptance window
    BUSINESS_CLOSE_HOUR: int = 23  # 11:00 PM (24h)

    # Automatically load from a .env file if it exists
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_cors_origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production" or os.getenv("VERCEL_ENV") == "production"



settings = Settings()
