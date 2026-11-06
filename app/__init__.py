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
        user = db.session.get(User, int(user_id))
        return user if user is not None and user.is_active else None
    except ValueError:
        return None


def create_app(config_name: str = 'default') -> Flask:
    app = Flask(__name__)

    app.config.from_object(config[config_name])
    secret_key = os.getenv('SECRET_KEY')
    unsafe_secret_values = {'dev-secret-key', 'your-secret-key-here', 'change-me'}
    if config_name == 'production' and (
        not secret_key
        or len(secret_key) < 32
        or secret_key.strip().lower() in unsafe_secret_values
    ):
        raise RuntimeError('Configura una SECRET_KEY segura antes de iniciar en producción')
    app.config['SECRET_KEY'] = secret_key or app.config.get('SECRET_KEY', 'dev-secret-key')
    app.config['CORS_ORIGINS'] = [
        origin.strip()
        for origin in os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')
        if origin.strip()
    ]
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = (
        True if config_name == 'production'
        else os.getenv('SESSION_COOKIE_SECURE', 'False').lower() in ('1', 'true', 'yes')
    )

    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']},}, supports_credentials=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import jsonify

        return jsonify({'success': False, 'message': 'Debes iniciar sesión'}), 401

    register_routes(app)
    register_admin_commands(app)

    return app


def register_admin_commands(app: Flask) -> None:
    import click
    from email_validator import EmailNotValidError, validate_email
    from werkzeug.security import generate_password_hash

    from app.models.users import User

    @app.cli.command('admin-create')
    @click.option('--email', prompt=True, help='Correo de la cuenta administradora.')
    @click.option('--name', 'full_name', prompt=True, help='Nombre del administrador.')
    @click.password_option(confirmation_prompt=True, help='Contraseña de la cuenta.')
    def create_admin(email: str, full_name: str, password: str) -> None:
        """Crea o promueve una cuenta administradora desde la consola local."""
        try:
            normalized_email = validate_email(email.strip(), check_deliverability=False).normalized
        except EmailNotValidError as error:
            raise click.ClickException('Debes proporcionar un email válido.') from error
        if not normalized_email or not full_name.strip() or len(full_name.strip()) > 255:
            raise click.ClickException('Debes proporcionar un nombre y un email válido.')
        if len(password) < 8:
            raise click.ClickException('La contraseña debe tener al menos 8 caracteres.')

        user = User.query.filter_by(email=normalized_email).first()
        if user is None:
            user = User(email=normalized_email, full_name=full_name.strip(), password_hash='')
            db.session.add(user)
        user.full_name = full_name.strip()
        user.password_hash = generate_password_hash(password)
        user.is_admin = True
        user.is_active = True
        db.session.commit()
        click.echo(f'Cuenta administradora lista: {normalized_email}')