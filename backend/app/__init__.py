import os
from flask import Flask
from flask_cors import CORS
from .extensions import db
from .routes.items import items_bp
from .routes.users import users_bp


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///dev.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    CORS(app, origins=['http://localhost:8100', 'http://localhost:4200'])

    db.init_app(app)

    app.register_blueprint(items_bp)
    app.register_blueprint(users_bp)

    @app.route('/health')
    def health():
        return {'status': 'ok'}

    return app

