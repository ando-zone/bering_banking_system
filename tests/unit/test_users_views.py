import os
import pytest
from unittest import mock

from app import db, create_app
from app.models import User


@pytest.fixture
def app():
    test_config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///{}".format(
            os.path.join(os.path.dirname(__file__), "test.db")
        ),
        "SECRET_KEY": "test_secret_key",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "BANK_ID": "555511",
    }
    app = create_app(test_config)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def logged_in_client(client):
    user = create_test_user()
    login(client, user.email, "password123")
    return client


def login(client, email, password):
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    assert "message" in response.json
    assert response.json["message"] == "Logged in successfully"


def create_test_user():
    user = User(
        name="testuser", email="testuser@example.com", password="password123"
    )
    db.session.add(user)
    db.session.commit()
    return user


def test_get_user_info(logged_in_client):
    response = logged_in_client.get("/users/me")
    assert response.status_code == 200
    assert "name" in response.json
    assert response.json["name"] == "testuser"
    assert "e-mail" in response.json
    assert response.json["e-mail"] == "testuser@example.com"


@mock.patch("app.views.users_views.current_app.logger")
def test_get_user_info_unauthenticated(mock_logging, client):
    response = client.get("/users/me")
    assert response.status_code == 302
    assert response.location == "/auth/login"


@mock.patch("app.views.users_views.current_app.logger")
def test_update_user_info(mock_logging, logged_in_client):
    new_name = "newuser"
    new_password = "newpassword"
    current_password = "password123"

    response = logged_in_client.put(
        "/users/me",
        json={
            "name": new_name,
            "current_password": current_password,
            "new_password": new_password,
            "new_password_again": new_password,
        },
    )
    assert response.status_code == 200
    assert "name" in response.json
    assert response.json["name"] == new_name

    user = User.query.filter_by(email="testuser@example.com").first()
    assert user.name == new_name
    assert user.verify_password(new_password)


@mock.patch("app.views.users_views.current_app.logger")
def test_update_user_info_with_incorrect_password(
    mock_logging, logged_in_client
):
    new_name = "newuser"
    new_password = "newpassword"
    current_password = "incorrectpassword"

    response = logged_in_client.put(
        "/users/me",
        json={
            "name": new_name,
            "current_password": current_password,
            "new_password": new_password,
            "new_password_again": new_password,
        },
    )
    assert response.status_code == 400
    assert "error" in response.json
    assert response.json["error"] == "Current password is incorrect."

    user = User.query.filter_by(email="testuser@example.com").first()
    assert user.name == "testuser"
    assert user.verify_password("password123")
