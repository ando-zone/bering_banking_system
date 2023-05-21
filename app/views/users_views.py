from flask import Blueprint, jsonify, request, g, current_app
from flask.views import MethodView

from app import db
from app.models import User
from app.views.auth_views import login_required

bp = Blueprint("users", __name__, url_prefix="/users")


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
            f"User info updated successfully for user id {user_id}"
        )

        return jsonify(user.to_dict()), 200

    def delete(self):
        user_id = g.user.id
        user = User.query.get(user_id)

        db.session.delete(user)
        db.session.commit()

        current_app.logger.info(f"Deleted user account for user id {user_id}")

        return jsonify({"message": "Account deleted successfully"}), 200


bp.add_url_rule("/me", view_func=MeView.as_view("me"))
