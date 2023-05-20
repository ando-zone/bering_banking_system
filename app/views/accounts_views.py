import random

from flask import Blueprint, jsonify, request, g, current_app
from flask.views import MethodView

from app import db
from app.models import Account, Card, AccountNumber
from app.views.auth_views import login_required

bp = Blueprint("accounts", __name__, url_prefix="/accounts")


class AccountListView(MethodView):
    decorators = [login_required]

    def get(self):
        user_id = g.user.id
        accounts = Account.query.filter_by(user_id=user_id).all()

        accounts_list = [account.to_dict() for account in accounts]

        return jsonify({"accounts": accounts_list}), 200

    def post(self):
        user_id = g.user.id
        name = request.json.get("name")
        password = request.json.get("password")
        error = None

        if not name:
            error = "Name is required."
        elif not password:
            error = "Password is required."

        if error is None:
            bank_id = current_app.config.get("BANK_ID")
            account_number = bank_id + "".join(
                random.choice("0123456789") for _ in range(7)
            )
            while AccountNumber.query.get(account_number) is not None:
                account_number = bank_id + "".join(
                    random.choice("0123456789") for _ in range(7)
                )

            new_account = Account(
                user_id=user_id,
                name=name,
                password=password,
                account_number=account_number,
            )
            new_account_number = AccountNumber(number=account_number)
            db.session.add(new_account_number)
            db.session.add(new_account)
            db.session.commit()
            return (
                jsonify(
                    {
                        "message": "Account created successfully",
                        "account": new_account.to_dict(),
                    }
                ),
                201,
            )

        return jsonify({"error": error}), 400


class AccountView(MethodView):
    decorators = [login_required]

    def get(self, account_id):
        account = Account.query.get(account_id)

        if account is None:
            return jsonify({"error": "Account not found"}), 404

        if account.user_id != g.user.id:
            return jsonify({"error": "Permission denied"}), 403

        return jsonify(account.to_dict_in_detail()), 200

    def put(self, account_id):
        account = Account.query.get(account_id)

        if account is None:
            return jsonify({"error": "Account not found"}), 404

        if account.user_id != g.user.id:
            return jsonify({"error": "Permission denied"}), 403

        account.name = request.json.get("name", account.name)
        previous_password = request.json.get("previous_password", None)
        new_password = request.json.get("new_password", None)

        if new_password:
            if previous_password is None:
                return (
                    jsonify(
                        {
                            "error": "Previous password is required to change password"
                        }
                    ),
                    400,
                )

            is_verified_password = account.verify_password(previous_password)
            if not is_verified_password:
                return jsonify({"error": "Incorrect previous password"}), 400

            account.password = new_password

        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Account updated successfully",
                    "account": account.to_dict_in_detail(),
                }
            ),
            200,
        )

    def delete(self, account_id):
        account = Account.query.get(account_id)

        if account is None:
            return jsonify({"error": "Account not found"}), 404

        if account.user_id != g.user.id:
            return jsonify({"error": "Permission denied"}), 403

        db.session.delete(account)
        db.session.commit()

        return jsonify({"message": "Account deleted successfully"}), 200


class AccountCardListView(MethodView):
    decorators = [login_required]

    def get(self, account_id):
        user_id = g.user.id
        cards = Card.query.filter_by(
            user_id=user_id, account_id=account_id
        ).all()

        cards_list = [card.to_dict() for card in cards]

        return jsonify({"cards": cards_list}), 200

    def post(self, account_id):
        user_id = g.user.id
        card_number = request.json.get("card_number")
        error = None

        if not card_number:
            error = "Card number is required."
        elif len(card_number) != 16:
            error = "Card number should be 16 digits."
        elif Card.query.filter_by(card_number=card_number).first() is not None:
            error = "A card with number '{}' is already registered.".format(
                card_number
            )

        if error is None:
            new_card = Card(
                user_id=user_id, account_id=account_id, card_number=card_number
            )
            db.session.add(new_card)
            db.session.commit()
            return (
                jsonify(
                    {
                        "message": "Card registered successfully",
                        "card": new_card.to_dict(),
                    }
                ),
                201,
            )

        return jsonify({"error": error}), 400


class AccountCardView(MethodView):
    decorators = [login_required]

    def get(self, account_id, card_id):
        card = Card.query.filter_by(id=card_id, account_id=account_id).first()

        if card is None:
            return jsonify({"error": "Card not found"}), 404

        if card.user_id != g.user.id:
            return jsonify({"error": "Permission denied"}), 403

        return jsonify(card.to_dict()), 200

    def delete(self, account_id, card_id):
        card = Card.query.filter_by(id=card_id, account_id=account_id).first()

        if card is None:
            return jsonify({"error": "Card not found"}), 404

        if card.user_id != g.user.id:
            return jsonify({"error": "Permission denied"}), 403

        db.session.delete(card)
        db.session.commit()

        return jsonify({"message": "Card deleted successfully"}), 200


bp.add_url_rule("/", view_func=AccountListView.as_view("account_list"))
bp.add_url_rule(
    "/<int:account_id>", view_func=AccountView.as_view("account_detail")
)
bp.add_url_rule(
    "/<int:account_id>/cards",
    view_func=AccountCardListView.as_view("account_card_list"),
)
bp.add_url_rule(
    "/<int:account_id>/cards/<int:card_id>",
    view_func=AccountCardView.as_view("account_card_detail"),
)
