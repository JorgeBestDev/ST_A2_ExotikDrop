import os
from pathlib import Path

from dotenv import load_dotenv

# Carga las variables de entorno desde un archivo .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


# Normaliza la URL de la base de datos para que sea compatible con SQLAlchemy
# En este proyecto se usa psycopg2-binary, por lo que el driver correcto es postgresql+psycopg2://
def _normalize_database_url(url: str | None) -> str:
    if not url:
        return "postgresql+psycopg2://postgres:postgres@localhost:5432/exotikdrop"

    cleaned = url.strip().strip("\"'")
    if cleaned.startswith("postgresql://"):
        return "postgresql+psycopg2://" + cleaned[len("postgresql://") :]
    return cleaned

#configuración de la aplicación Flask
class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "dev-admin-key")
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(os.getenv("DATABASE_URL"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

#clases de configuración para diferentes entornos
class DevelopmentConfig(Config):
    DEBUG = True

#clase de configuración para el entorno de producción
class ProductionConfig(Config):
    DEBUG = False

#clase de configuración para el entorno de pruebas
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    ADMIN_API_KEY = "dev-admin-key"

#configuración de la aplicación Flask según el entorno
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}