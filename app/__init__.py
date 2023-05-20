from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import logging

from .config import get_db_uri, get_secret_key

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = get_db_uri()
    app.config["SECRET_KEY"] = get_secret_key()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ORM
    db.init_app(app)
    migrate.init_app(app, db)
    from . import models

    # blueprint
    from .views import main_views, auth_views, account_views, card_views
    app.register_blueprint(main_views.bp)
    app.register_blueprint(auth_views.bp)
    app.register_blueprint(account_views.bp)
    app.register_blueprint(card_views.bp)

    return app
