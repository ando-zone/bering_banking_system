import os
import pytest

from app import db, create_app
from app.models import User


@pytest.fixture
def app():
    test_config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///{}".format(os.path.join(os.path.dirname(__file__), "test.db")),
        "SECRET_KEY": "test_secret_key",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "BANK_ID": "555511"
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


def test_create_user(client):
    response = client.post(
        "/auth/create",
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "password123",
        },
    )
    data = response.get_json()
    assert response.status_code == 200
    assert data["message"] == "Account created successfully"


def test_login(client):
    user = User(name="testuser", email="testuser@example.com", password="password123")
    db.session.add(user)
    db.session.commit()

    response = client.post(
        "/auth/login",
        json={"email": "testuser@example.com", "password": "password123"},
    )
    data = response.get_json()
    assert response.status_code == 200
    assert data["message"] == "Logged in successfully"


def test_logout(client):
    user = User(name="testuser", email="testuser@example.com", password="password123")
    db.session.add(user)
    db.session.commit()

    response = client.post(
        "/auth/login",
        json={"email": "testuser@example.com", "password": "password123"},
    )
    assert response.status_code == 200

    response = client.post("/auth/logout")
    data = response.get_json()
    assert response.status_code == 200
    assert data["message"] == "Logged out successfully"


def login(client, email, password):
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    assert "message" in response.json
    assert response.json["message"] == "Logged in successfully"