import os
import pytest
import random
from unittest import mock

from app import db, create_app
from app.models import Card, Account, User


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


def create_test_account(user_id):
    account_number = "555511" + "".join(
        random.choice("0123456789") for _ in range(7)
    )
    account = Account(
        user_id=user_id,
        name="Test Account",
        password="password",
        account_number=account_number,
    )
    db.session.add(account)
    db.session.commit()
    return account


def create_test_card(user_id, account_id):
    card_number = "".join(random.choice("0123456789") for _ in range(16))
    card = Card(user_id=user_id, account_id=account_id, card_number=card_number)
    db.session.add(card)
    db.session.commit()
    return card


@mock.patch("app.views.users_views.current_app.logger")
def test_get_card_list_from_user(mock_logging, client):
    user = create_test_user()
    login(client, user.email, "password123")
    account = create_test_account(user.id)
    card = create_test_card(user.id, account.id)

    response = client.get("/cards/")
    assert response.status_code == 200
    assert "cards" in response.json
    assert len(response.json["cards"]) == 1
    assert response.json["cards"][0]["id"] == card.id


@mock.patch("app.views.users_views.current_app.logger")
def test_get_card_detail(mock_logging, client):
    user = create_test_user()
    login(client, user.email, "password123")
    account = create_test_account(user.id)
    card = create_test_card(user.id, account.id)

    response = client.get(f"/cards/{card.id}")
    assert response.status_code == 200
    assert "id" in response.json
    assert response.json["id"] == card.id
    assert "card_number" in response.json
    assert response.json["card_number"] == card.card_number


@mock.patch("app.views.users_views.current_app.logger")
def test_enable_card(mock_logging, client):
    user = create_test_user()
    login(client, user.email, "password123")
    account = create_test_account(user.id)
    card = create_test_card(user.id, account.id)

    response = client.put(f"/cards/{card.id}/enable")
    assert response.status_code == 200
    assert "id" in response.json
    assert response.json["id"] == card.id
    assert "status" in response.json
    assert response.json["status"] == "enabled"


@mock.patch("app.views.users_views.current_app.logger")
def test_enable_card_not_authorized(mock_logging, client):
    user1 = User(
        name="user1", email="user1@example.com", password="password123"
    )
    db.session.add(user1)
    db.session.commit()

    account1 = create_test_account(user1.id)
    card1 = create_test_card(user1.id, account1.id)

    user2 = User(
        name="otheruser", email="otheruser@example.com", password="password123"
    )
    db.session.add(user2)
    db.session.commit()

    login(client, user2.email, "password123")
    response = client.put(f"/cards/{card1.id}/enable")
    assert response.status_code == 403
    assert "error" in response.json
    assert response.json["error"] == "Not authorized"


@mock.patch("app.views.users_views.current_app.logger")
def test_disable_card(mock_logging, client):
    user = create_test_user()
    login(client, user.email, "password123")
    account = create_test_account(user.id)
    card = create_test_card(user.id, account.id)
    card.enable()

    response = client.put(f"/cards/{card.id}/disable")
    assert response.status_code == 200
    assert "id" in response.json
    assert response.json["id"] == card.id
    assert "status" in response.json
    assert response.json["status"] == "disabled"


@mock.patch("app.views.users_views.current_app.logger")
def test_disable_card_not_authorized(mock_logging, client):
    user1 = User(
        name="user1", email="user1@example.com", password="password123"
    )
    db.session.add(user1)
    db.session.commit()

    account1 = create_test_account(user1.id)
    card1 = create_test_card(user1.id, account1.id)
    card1.enable()

    user2 = User(
        name="otheruser", email="otheruser@example.com", password="password123"
    )
    db.session.add(user2)
    db.session.commit()

    login(client, user2.email, "password123")
    response = client.put(f"/cards/{card1.id}/disable")
    assert response.status_code == 403
    assert "error" in response.json
    assert response.json["error"] == "Not authorized"


@mock.patch("app.views.users_views.current_app.logger")
def test_withdraw(mock_logging, client):
    user = create_test_user()
    login(client, user.email, "password123")
    account = create_test_account(user.id)
    card = create_test_card(user.id, account.id)
    card.enable()
    card.deposit(account, 100000)

    response = client.post(
        f"/cards/{card.id}/withdraw",
        json={"amount": 50000, "account_password": "password"},
    )
    assert response.status_code == 200
    assert "message" in response.json
    assert response.json["message"] == f"Withdrawing {50000} from active card."
    assert "card" in response.json
    assert "balance" in response.json
    assert response.json["balance"] == 50000


@mock.patch("app.views.users_views.current_app.logger")
def test_withdraw_insufficient_balance(mock_logging, client):
    user = create_test_user()
    login(client, user.email, "password123")
    account = create_test_account(user.id)
    card = create_test_card(user.id, account.id)
    card.enable()

    response = client.post(
        f"/cards/{card.id}/withdraw",
        json={"amount": 50000, "account_password": "password"},
    )
    assert response.status_code == 200
    assert "message" in response.json
    assert (
        response.json["message"]
        == "FAILED: Insufficient balance for withdrawal."
    )
    assert "card" in response.json
    assert "balance" in response.json
    assert response.json["balance"] == 0


@mock.patch("app.views.users_views.current_app.logger")
def test_withdraw_not_authorized(mock_logging, client):
    user1 = create_test_user()
    account = create_test_account(user1.id)
    card = create_test_card(user1.id, account.id)
    card.enable()

    user2 = User(
        name="otheruser", email="otheruser@example.com", password="password123"
    )
    db.session.add(user2)
    db.session.commit()

    login(client, user2.email, "password123")
    response = client.post(
        f"/cards/{card.id}/withdraw",
        json={"amount": 50000, "account_password": "password"},
    )
    assert response.status_code == 403
    assert "error" in response.json
    assert response.json["error"] == "Not authorized"


@mock.patch("app.views.users_views.current_app.logger")
def test_deposit(mock_logging, client):
    user = create_test_user()
    login(client, user.email, "password123")
    account = create_test_account(user.id)
    card = create_test_card(user.id, account.id)
    card.enable()

    response = client.post(
        f"/cards/{card.id}/deposit",
        json={"amount": 50000},
    )
    assert response.status_code == 200
    assert "message" in response.json
    assert response.json["message"] == "Depositing 50000 to active card."
    assert "card" in response.json
    assert "balance" in response.json
    assert response.json["balance"] == 50000


@mock.patch("app.views.users_views.current_app.logger")
def test_deposit_not_authorized(mock_logging, client):
    user1 = create_test_user()
    account = create_test_account(user1.id)
    card = create_test_card(user1.id, account.id)
    card.enable()

    user2 = User(
        name="otheruser", email="otheruser@example.com", password="password123"
    )
    db.session.add(user2)
    db.session.commit()

    login(client, user2.email, "password123")

    response = client.post(
        f"/cards/{card.id}/deposit",
        json={"amount": 50000},
    )
    assert response.status_code == 403
    assert "error" in response.json
    assert response.json["error"] == "Not authorized"


@mock.patch("app.views.users_views.current_app.logger")
def test_check_balance_using_card(mock_logging, client):
    user = create_test_user()
    login(client, user.email, "password123")
    account = create_test_account(user.id)
    card = create_test_card(user.id, account.id)
    card.enable()

    response = client.get(f"/cards/{card.id}/balance")
    assert response.status_code == 200
    assert "balance" in response.json
    assert response.json["balance"] == card.account.balance


@mock.patch("app.views.users_views.current_app.logger")
def test_check_balance_using_card_not_authorized(mock_logging, client):
    user1 = create_test_user()
    account = create_test_account(user1.id)
    card = create_test_card(user1.id, account.id)
    card.enable()

    user2 = User(
        name="otheruser", email="otheruser@example.com", password="password123"
    )
    db.session.add(user2)
    db.session.commit()

    login(client, user2.email, "password123")

    response = client.get(f"/cards/{card.id}/balance")
    assert response.status_code == 403
    assert "error" in response.json
    assert response.json["error"] == "Not authorized"
