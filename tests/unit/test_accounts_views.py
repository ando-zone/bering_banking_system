import os
import pytest
from unittest import mock

from app import db, create_app
from app.models import User, Account, Card


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


def login(client, email, password):
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    assert "message" in response.json
    assert response.json["message"] == "Logged in successfully"


def create_test_user():
    user = User(name="testuser", email="testuser@example.com", password="password123")
    db.session.add(user)
    db.session.commit()
    return user


def create_test_account(user_id):
    account_number = "5555111234567"
    account = Account(user_id=user_id, name="Test Account", password="password", account_number=account_number)
    db.session.add(account)
    db.session.commit()
    return account


def create_test_card(account_id):
    card = Card(account_id=account_id, card_number="1234567890123456")
    db.session.add(card)
    db.session.commit()
    return card


@mock.patch("app.views.auth_views.current_app.logger")
def test_get_user_account_unauthenticated(mock_logging, client):
    response = client.get("/accounts/")
    assert response.status_code == 302  
    assert response.location == "/auth/login"


def test_get_user_account(client):
    user = create_test_user()
    login(client, user.email, "password123")
    account = create_test_account(user.id)

    response = client.get("/accounts/")
    assert response.status_code == 200
    assert "accounts" in response.json
    assert len(response.json["accounts"]) == 1
    assert response.json["accounts"][0]["name"] == account.name


def test_create_user_account(client):
    user = create_test_user()
    login(client, user.email, "password123")

    response = client.post(
        "/accounts/",
        json={
            "name": "Test Account",
            "password": "password",
        },
    )

    print(response.json)
    assert response.status_code == 201
    assert "account" in response.json
    assert response.json["account"]["name"] == "Test Account"
    assert "message" in response.json
    assert response.json["message"] == "Account created successfully"


def test_account_card_list_view_get(client):
    user = create_test_user()
    login(client, user.email, "password123")
    account = create_test_account(user.id)
    card = create_test_card(account.id)

    response = client.get(f"/accounts/{account.id}/cards")
    assert response.status_code == 200
    assert "cards" in response.json
    assert len(response.json["cards"]) == 1
    assert response.json["cards"][0]["id"] == card.id


def test_account_card_list_view_post(client):
    user = create_test_user()
    login(client, user.email, "password123")
    account = create_test_account(user.id)

    response = client.post(f"/accounts/{account.id}/cards", json={"card_number": "1234567890123456"})
    assert response.status_code == 201
    assert "card" in response.json
    assert response.json["card"]["account_id"] == account.id
    assert response.json["card"]["card_number"] == "1234567890123456"


def test_account_card_list_view_post_invalid_card_number(client):
    user = create_test_user()
    login(client, user.email, "password123")
    account = create_test_account(user.id)
    create_test_card(account.id)

    response = client.post(f"/accounts/{account.id}/cards", json={"card_number": "1234567890123456"})
    assert response.status_code == 400
    assert "error" in response.json
    assert response.json["error"] == "A card with number '1234567890123456' is already registered."
