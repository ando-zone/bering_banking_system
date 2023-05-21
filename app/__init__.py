import logging

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from .config import get_db_uri, get_secret_key

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = get_db_uri()
    app.config["SECRET_KEY"] = get_secret_key()
    app.config.from_pyfile("config.py")

    # logging
    logging.basicConfig(
        filename="app.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)

    # ORM
    db.init_app(app)
    migrate.init_app(app, db)
    from . import models

    # blueprint
    from .views import (
        index_views,
        auth_views,
        accounts_views,
        cards_views,
        users_views,
    )

    app.register_blueprint(index_views.bp)
    app.register_blueprint(auth_views.bp)
    app.register_blueprint(users_views.bp)
    app.register_blueprint(accounts_views.bp)
    app.register_blueprint(cards_views.bp)

    return app
