from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

#inicializa la extensión SQLAlchemy y Migrate para la aplicación Flask
db=SQLAlchemy()
migrate=Migrate()