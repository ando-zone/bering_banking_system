from enum import Enum as PyEnum
from sqlalchemy import Enum
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.card_state import Enabled, Disabled


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128))  # storing password hash instead of plaintext
    accounts = db.relationship('Account', backref='user', lazy=True)
    cards = db.relationship('Card', backref='user', lazy=True)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        account_count = len(self.accounts)
        card_count = len(self.cards)

        return {
            "id": self.id,
            "e-mail": self.email,
            "name": self.name,
            "account_count": account_count,
            "card_count": card_count
        }


class AccountNumber(db.Model):
    number = db.Column(db.String(12), primary_key=True)


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(12), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128))
    balance = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cards = db.relationship('Card', backref='account', lazy=True)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "account_number": self.account_number,
            "account_owner": self.user.name,
            "name": self.name,
            "balance": self.balance
        }

    def to_dict_in_detail(self):
        card_ids = [card.id for card in self.cards]
        return {
            "id": self.id,
            "account_number": self.account_number,
            "account_owner": self.user.name,
            "name": self.name,
            "balance": self.balance,
            "cards": card_ids
        }


class CardStatus(PyEnum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_number = db.Column(db.String(16), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    state = db.Column(Enum(CardStatus), nullable=False, default=CardStatus.DISABLED) 

    def enable(self):
        self.state = CardStatus.ENABLED

    def disable(self):
        self.state = CardStatus.DISABLED

    def verify_owner(self, user):
        return self.user_id == user.id

    def withdraw(self, account, amount):
        if self.state == CardStatus.ENABLED:
            return Enabled().withdraw(account, amount)
        else:
            return Disabled().withdraw(account, amount)

    def deposit(self, account, amount):
        if self.state == CardStatus.ENABLED:
            return Enabled().deposit(account, amount)
        else:
            return Disabled().deposit(account, amount)

    def to_dict(self):
        return {
            "id": self.id,
            "user_name": self.user.name,
            "account_id": self.account.id,
            "card_number": self.card_number,
            "status": self.state.value.lower()
        }
