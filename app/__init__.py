import os

from flask import Flask
from flask_cors import CORS

from app.config import config
from app.extensions import db, login_manager, migrate
from app import models  # noqa: F401  # fuerza la carga de todos los modelos SQLAlchemy
from app.routes import register_routes


@login_manager.user_loader
def load_user(user_id: str):
    from app.models.users import User

    try:
        return db.session.get(User, int(user_id))
    except ValueError:
        return None


def create_app(config_name: str = 'default') -> Flask:
    app = Flask(__name__)

    app.config.from_object(config[config_name])
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', app.config.get('SECRET_KEY', 'dev-secret-key'))
    app.config['CORS_ORIGINS'] = [
        origin.strip()
        for origin in os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')
        if origin.strip()
    ]
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() in ('1', 'true', 'yes')

    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']},}, supports_credentials=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import jsonify

        return jsonify({'success': False, 'message': 'Debes iniciar sesión'}), 401

    register_routes(app)

    return app