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
    password_hash = db.Column(db.String(128))  # storing password hash instead of plaintext
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
            "user_name": self.user.name,
            "name": self.name,
            "balance": self.balance
        }


class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_number = db.Column(db.String(16), unique=True, nullable=False)  # unique card number
    status = db.Column(db.String(100), default='disabled')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # reference to the User
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)  # reference to the Account

    @property
    def state(self):
        return Enabled() if self.status == 'enabled' else Disabled()

    def enable(self):
        self.status = self.state.enable().__class__.__name__.lower()

    def disable(self):
        self.status = self.state.disable().__class__.__name__.lower()

    def verify_owner(self, user):
        return self.user_id == user.id

    def withdraw(self, account, amount):
        return self.state.withdraw(account, amount)

    def deposit(self, account, amount):
        return self.state.deposit(account, amount)

    def to_dict(self):
        return {
            "id": self.id,
            "user_name": self.user.name,
            "account_id": self.account.id,
            "card_number": self.card_number,
            "status": self.status
        }