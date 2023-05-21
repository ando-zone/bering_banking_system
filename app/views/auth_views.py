import functools

from flask import (
    Blueprint,
    request,
    session,
    jsonify,
    g,
    redirect,
    url_for,
    current_app,
)
from flask.views import MethodView

from app.models import User
from app import db

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)
        current_app.logger.info(f"Loaded user with id {user_id}")


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            current_app.logger.warning("Unauthorized access attempt")
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


class MeView(MethodView):
    decorators = [login_required]

    def get(self):
        user_id = g.user.id
        user = User.query.get(user_id)

        current_app.logger.info(f"Fetched user info for id {user_id}")

        return jsonify(user.to_dict()), 200

    def put(self):
        user_id = g.user.id
        user = User.query.get(user_id)

        username = request.json.get("name", None)
        current_password = request.json.get("current_password", None)
        new_password = request.json.get("new_password", None)
        new_password_again = request.json.get("new_password_again", None)

        error = None

        if username:
            user.name = username
            db.session.commit()
            current_app.logger.info(
                f"Username updated successfully for user id {user_id}"
            )

        if new_password:
            if not current_password:
                error = "Current password is required."
            elif not user.verify_password(current_password):
                error = "Current password is incorrect."
            elif new_password != new_password_again:
                error = "Two new passwords are not equal to each other."

            if error is not None:
                current_app.logger.error(error)
                return jsonify({"error": error}), 400

            user.password = new_password
            db.session.commit()
            current_app.logger.info(
                f"Password updated successfully for user id {user_id}"
            )

        return jsonify(user.to_dict()), 200

    def delete(self):
        user_id = g.user.id
        user = User.query.get(user_id)

        db.session.delete(user)
        db.session.commit()

        current_app.logger.info(f"Deleted user account for user id {user_id}")

        return jsonify({"message": "Account deleted successfully"}), 200


class UserCreateView(MethodView):
    def post(self):
        username = request.json.get("username")
        email = request.json.get("email")
        password = request.json.get("password")
        error = None

        if not username:
            error = "Username is required."
        elif not email:
            error = "E-mail is required."
        elif not password:
            error = "Password is required."
        elif User.query.filter_by(email=email).first() is not None:
            error = "E-mail {} is already registered.".format(email)

        if error is None:
            new_user = User(name=username, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            current_app.logger.info(f"Created new user with email {email}")

            return jsonify({"message": "Account created successfully"})

        current_app.logger.error(f"Account creation failed: {error}")

        return jsonify({"error": error}), 400


class LogInView(MethodView):
    def get(self):
        if g.user:
            current_app.logger.info(f"User already logged in.")
            return jsonify({"message": "You are already logged in!"}), 200

        current_app.logger.info(f"Prompting user to log in.")

        return jsonify({"message": "Please Log into Bering Bank!"}), 200

    def post(self):
        username = request.json.get("username")
        password = request.json.get("password")
        error = None

        user = User.query.filter_by(name=username).first()

        if user is None:
            error = "Incorrect username."
        elif not user.verify_password(password):
            error = "Incorrect password."

        if error is None:
            session.clear()
            session["user_id"] = user.id
            current_app.logger.info(f"User {username} logged in successfully.")

            return jsonify({"message": "Logged in successfully"})

        current_app.logger.error(
            f"Login attempt failed for user {username}: {error}"
        )

        return jsonify({"error": error}), 400


class LogOutView(MethodView):
    decorators = [login_required]

    def post(self):
        session.clear()
        current_app.logger.info(f"User logged out successfully.")

        return jsonify({"message": "Logged out successfully"})


bp.add_url_rule("/me", view_func=MeView.as_view("me"))
bp.add_url_rule("/create", view_func=UserCreateView.as_view("create_user"))
bp.add_url_rule("/login", view_func=LogInView.as_view("login"))
bp.add_url_rule("/logout", view_func=LogOutView.as_view("logout"))
