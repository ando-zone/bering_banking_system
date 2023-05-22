import random

from flask import Blueprint, jsonify, request, g, current_app
from flask.views import MethodView

from app import db
from app.models import Account, Card, AccountNumber
from app.views.auth_views import login_required

bp = Blueprint("accounts", __name__, url_prefix="/accounts")


def create_account_number() -> str:
    """새로운 계좌 번호를 생성하는 메서드.

    Note:
        만약 새롭게 생성한 계좌 번호가 Database에서 특정 계좌가 이미 사용하고 있거나
        현재 소멸된 계좌가 사용했던 번호일 경우, 새로운 번호를 겹치지 않을 때 까지 재생성함.
        이미 다른 계좌가 사용하고 있는 계좌 번호 혹은 소멸된 계좌가 사용했던 계좌 번호 모두
        AccountNumber 모델을 통해 확인할 수 있다.

    Returns:
        str: 13자리의 계좌 번호이며 앞 6자리는 은행 식별 번호가 포함된다.

    Examples:
        >>> create_account_number()
        "5555110123456"
    """
    bank_id = current_app.config.get("BANK_ID")
    account_number = bank_id + "".join(
        random.choice("0123456789") for _ in range(7)
    )
    while db.session.get(AccountNumber, account_number) is not None:
        account_number = bank_id + "".join(
            random.choice("0123456789") for _ in range(7)
        )

    return account_number


class AccountListView(MethodView):
    decorators = [login_required]

    def get(self):
        user_id = g.user.id
        accounts = Account.query.filter_by(user_id=user_id).all()

        accounts_list = [account.to_dict() for account in accounts]
        current_app.logger.info(
            f"Fetched {len(accounts_list)} accounts for user id {user_id}"
        )

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
            account_number = create_account_number()
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

            current_app.logger.info(
                f"Account created successfully for user id {user_id}"
            )

            return (
                jsonify(
                    {
                        "message": "Account created successfully",
                        "account": new_account.to_dict(),
                    }
                ),
                201,
            )

        current_app.logger.error(error)

        return jsonify({"error": error}), 400


class AccountView(MethodView):
    decorators = [login_required]

    def get(self, account_id):
        account = Account.query.get(account_id)

        if account is None:
            current_app.logger.error(f"Account id {account_id} not found")

            return jsonify({"error": "Account not found"}), 404

        if account.user_id != g.user.id:
            current_app.logger.error(
                f"Not authorized for user id {g.user.id} for account id {account_id}"
            )

            return jsonify({"error": "Not authorized"}), 403

        current_app.logger.info(f"Fetched details for account id {account_id}")

        return jsonify(account.to_dict_in_detail()), 200

    def put(self, account_id):
        account = Account.query.get(account_id)

        if account is None:
            current_app.logger.error(f"Account id {account_id} not found")

            return jsonify({"error": "Account not found"}), 404

        if account.user_id != g.user.id:
            current_app.logger.error(
                f"Not authorized for user id {g.user.id} for account id {account_id}"
            )

            return jsonify({"error": "Not authorized"}), 403

        account_name = request.json.get("name", None)
        current_password = request.json.get("current_password", None)
        new_password = request.json.get("new_password", None)
        new_password_again = request.json.get("new_password_again", None)

        if account_name:
            account.name = account_name

        if new_password:
            if current_password is None:
                current_app.logger.error(
                    "Previous password is required to change password"
                )
                db.session.rollback()

                return (
                    jsonify(
                        {
                            "error": "Previous password is required to change password"
                        }
                    ),
                    400,
                )
            elif new_password != new_password_again:
                current_app.logger.error(
                    "Two passwords are not equal to each other."
                )
                db.session.rollback()

                return (
                    jsonify(
                        {"error": "Two passwords are not equal to each other."}
                    ),
                    400,
                )

            is_verified_password = account.verify_password(current_password)
            if not is_verified_password:
                current_app.logger.error("Incorrect previous password")
                db.session.rollback()

                return jsonify({"error": "Incorrect previous password"}), 400

            account.password = new_password

        db.session.commit()

        current_app.logger.info(f"Account id {account_id} updated successfully")

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
            current_app.logger.error(f"Account id {account_id} not found")

            return jsonify({"error": "Account not found"}), 404

        if account.user_id != g.user.id:
            current_app.logger.error(
                f"Not authorized for user id {g.user.id} for account id {account_id}"
            )

            return jsonify({"error": "Not authorized"}), 403

        db.session.delete(account)
        db.session.commit()

        current_app.logger.info(f"Account id {account_id} deleted successfully")

        return jsonify({"message": "Account deleted successfully"}), 200


class AccountCardListView(MethodView):
    decorators = [login_required]

    def get(self, account_id):
        user_id = g.user.id
        cards = Card.query.filter_by(
            user_id=user_id, account_id=account_id
        ).all()

        cards_list = [card.to_dict() for card in cards]

        current_app.logger.info(f"Fetched cards for account id {account_id}")

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

            current_app.logger.info(
                f"Card registered successfully for account id {account_id}"
            )

            return (
                jsonify(
                    {
                        "message": "Card registered successfully",
                        "card": new_card.to_dict(),
                    }
                ),
                201,
            )

        current_app.logger.error(error)

        return jsonify({"error": error}), 400


class AccountCardView(MethodView):
    decorators = [login_required]

    def get(self, account_id, card_id):
        card = Card.query.filter_by(id=card_id, account_id=account_id).first()

        if card is None:
            current_app.logger.error(
                f"Card id {card_id} not found for account id {account_id}"
            )

            return jsonify({"error": "Card not found"}), 404

        if card.user_id != g.user.id:
            current_app.logger.error(
                f"Not authorized for user id {g.user.id} for card id {card_id}"
            )

            return jsonify({"error": "Not authorized"}), 403

        current_app.logger.info(
            f"Fetched card id {card_id} for account id {account_id}"
        )

        return jsonify(card.to_dict()), 200

    def delete(self, account_id, card_id):
        card = Card.query.filter_by(id=card_id, account_id=account_id).first()

        if card is None:
            current_app.logger.error(
                f"Card id {card_id} not found for account id {account_id}"
            )

            return jsonify({"error": "Card not found"}), 404

        if card.user_id != g.user.id:
            current_app.logger.error(
                f"Not authorized for user id {g.user.id} for card id {card_id}"
            )

            return jsonify({"error": "Not authorized"}), 403

        db.session.delete(card)
        db.session.commit()

        current_app.logger.info(
            f"Card id {card_id} deleted successfully for account id {account_id}"
        )

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
