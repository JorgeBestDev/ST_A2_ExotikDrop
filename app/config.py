import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def _normalize_database_url(url: str | None) -> str:
    if not url:
        database_path = BASE_DIR / "instance" / "exitdrop-dev.sqlite3"
        database_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{database_path.as_posix()}"

    cleaned = url.strip().strip("\"'")
    if cleaned.startswith("postgresql://"):
        return "postgresql+psycopg2://" + cleaned[len("postgresql://"):]
    return cleaned


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "dev-admin-key")
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(os.getenv("DATABASE_URL"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    ADMIN_API_KEY = "dev-admin-key"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
