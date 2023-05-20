from flask import (
    Blueprint,
    request,
    session,
    redirect,
    url_for,
    jsonify,
    g
)

from app.models import User
from app import db

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/create_user", methods=("GET", "POST",))
def create_user():
    if request.method == "POST":
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
            return jsonify({"message": "Account created successfully"})

        return jsonify({"error": error}), 400
    
    return jsonify({"message": "Please Sign into Bering Bank!"}), 200


# TODO@Ando: 근데 현금 인출 및 예금 기능에 로그인이 필요한가? YES
@bp.route("/login", methods=("GET", "POST",))
def login():
    if request.method == "POST":
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
            return jsonify({"message": "Logged in successfully"})

        return jsonify({"error": error}), 401

    if g.user:
        return jsonify({"message": "You are already logged in!"}), 200

    return jsonify({"message": "Please Log into Bering Bank!"}), 200


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)


@bp.route("/logout")
def logout():
    if g.user is not None:
        session.clear()
        return jsonify({"message": "Logged out successfully"})

    return redirect(url_for("auth.login"))
