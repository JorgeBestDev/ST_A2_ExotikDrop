import os

from flask import Flask
from flask_cors import CORS

from app.config import config
from app.extensions import db, migrate
from app import models  # noqa: F401  # fuerza la carga de todos los modelos SQLAlchemy
from app.routes import register_routes


def create_app(config_name: str = 'default') -> Flask:
    app = Flask(__name__)

    app.config.from_object(config[config_name])
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', app.config.get('SECRET_KEY', 'dev-secret-key'))
    app.config['CORS_ORIGINS'] = os.getenv('CORS_ORIGINS', 'http://localhost:5173')

    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})

    db.init_app(app)
    migrate.init_app(app, db)

    register_routes(app)

    return app