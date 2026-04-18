import os
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from .extensions import db
from .routes.items import items_bp
from .routes.users import users_bp
from .routes.auth import auth_bp
from .routes.projects import projects_bp


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///dev.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-me')

    CORS(app, origins=['http://localhost:8100', 'http://localhost:4200'])
    JWTManager(app)
    db.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(projects_bp)

    @app.route('/health')
    def health():
        return {'status': 'ok'}

    return app
