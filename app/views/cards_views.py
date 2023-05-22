from flask import Blueprint, jsonify, request, g, current_app
from flask.views import MethodView

from app import db
from app.models import Card, Account
from app.card_state import Disabled, Enabled
from app.views.auth_views import login_required

bp = Blueprint("cards", __name__, url_prefix="/cards")


class CardListView(MethodView):
    decorators = [login_required]

    def get(self):
        user_id = g.user.id
        cards = Card.query.filter_by(user_id=user_id).all()

        card_list = [card.to_dict() for card in cards]

        return jsonify({"cards": card_list}), 200


class CardView(MethodView):
    decorators = [login_required]

    def get(self, card_id):
        card = Card.query.get(card_id)
        if card is None:
            error_msg = "Card not found"
            current_app.logger.error(error_msg)

            return jsonify({"error": "Card not found"}), 404

        if not card.verify_owner(g.user):
            error_msg = "Not authorized"
            current_app.logger.error(error_msg)

            return jsonify({"error": "Not authorized"}), 403

        return jsonify(card.to_dict()), 200


class EnableCardView(MethodView):
    decorators = [login_required]

    def put(self, card_id):
        card = Card.query.get(card_id)
        if card is None:
            error_msg = "Card not found"
            current_app.logger.error(error_msg)

            return jsonify({"error": "Card not found"}), 404

        if not card.verify_owner(g.user):
            error_msg = "Not authorized"
            current_app.logger.error(error_msg)

            return jsonify({"error": "Not authorized"}), 403

        if isinstance(card.state, Enabled):
            warning_msg = "The card is already enabled"
            current_app.logger.warning(warning_msg)

            return jsonify({"error": warning_msg}), 400

        card.enable()
        db.session.commit()

        current_app.logger.info("The card is successfully enabled")

        return jsonify(card.to_dict()), 200


class DisableCardView(MethodView):
    decorators = [login_required]

    def put(self, card_id):
        card = Card.query.get(card_id)
        if card is None:
            error_msg = "Card not found"
            current_app.logger.error(error_msg)

            return jsonify({"error": "Card not found"}), 404

        if not card.verify_owner(g.user):
            error_msg = "Not authorized"
            current_app.logger.error(error_msg)

            return jsonify({"error": "Not authorized"}), 403

        if isinstance(card.state, Disabled):
            warning_msg = "The card is already disabled"
            current_app.logger.warning(warning_msg)

            return jsonify({"warning": warning_msg}), 400

        card.disable()
        db.session.commit()

        current_app.logger.info("The card is successfully disabled")

        return jsonify(card.to_dict()), 200


class WithdrawView(MethodView):
    decorators = [login_required]

    def post(self, card_id):
        card = Card.query.get(card_id)
        if card is None:
            error_msg = "Card not found"
            current_app.logger.error(error_msg)

            return jsonify({"error": error_msg}), 404

        if not card.verify_owner(g.user):
            error_msg = "Not authorized"
            current_app.logger.error(error_msg)

            return jsonify({"error": error_msg}), 403

        account_id = card.account.id
        account = Account.query.get(account_id)

        if account is None:
            error_msg = "Account not found"
            current_app.logger.error("Account not found")

            return jsonify(error=error_msg), 404

        amount = request.json.get("amount")
        account_password = request.json.get("account_password")

        if not account.verify_password(account_password):
            error_msg = "Invalid account password"
            current_app.logger.error(error_msg)

            return jsonify({"error": error_msg}), 401

        # TODO@Ando: 일정 금액 이상 인출 시, 알림 이용하기. (알림 시스템 구축)
        is_successful, message = card.withdraw(account, amount)
        db.session.commit()

        balance = card.account.balance
        if is_successful:
            current_app.logger.info(f"{message}, now balance: {balance}")
        else:
            current_app.logger.warning(f"{message}, now balance: {balance}")

        return (
            jsonify(
                {
                    "message": message,
                    "card": card.to_dict(),
                    "balance": balance,
                }
            ),
            200,
        )


class DepositView(MethodView):
    decorators = [login_required]

    def post(self, card_id):
        card = Card.query.get(card_id)
        if card is None:
            error_msg = "Card not found"
            current_app.logger.error(error_msg)

            return jsonify({"error": "Card not found"}), 404

        if not card.verify_owner(g.user):
            error_msg = "Not authorized"
            current_app.logger.error(error_msg)

            return jsonify({"error": error_msg}), 403

        account_id = card.account.id
        account = Account.query.get(account_id)

        if account is None:
            error_msg = "Account not found"
            current_app.logger.error(error_msg)

            return jsonify(error=error_msg), 404

        amount = request.json.get("amount")

        message = card.deposit(account, amount)
        db.session.commit()

        balance = card.account.balance
        current_app.logger.info(f"{message}, now balance: {balance}")

        return (
            jsonify(
                {
                    "message": message,
                    "card": card.to_dict(),
                    "balance": balance,
                }
            ),
            200,
        )


class BalanceView(MethodView):
    decorators = [login_required]

    def get(self, card_id):
        card = Card.query.get(card_id)
        if card is None:
            error_msg = "Card not found"
            current_app.logger.error(error_msg)

            return jsonify({"error": error_msg}), 404

        if not card.verify_owner(g.user):
            error_msg = "Not authorized"
            current_app.logger.error(error_msg)

            return jsonify({"error": error_msg}), 403

        balance = card.account.balance
        current_app.logger.info(
            f"Balance check successful, now balance: {balance}"
        )

        return jsonify({"balance": balance}), 200


bp.add_url_rule("/", view_func=CardListView.as_view("card"))
bp.add_url_rule("/<int:card_id>", view_func=CardView.as_view("card_detail"))
bp.add_url_rule(
    "/<int:card_id>/enable", view_func=EnableCardView.as_view("enable_card")
)
bp.add_url_rule(
    "/<int:card_id>/disable", view_func=DisableCardView.as_view("disable_card")
)
bp.add_url_rule(
    "/<int:card_id>/withdraw", view_func=WithdrawView.as_view("card_withdraw")
)
bp.add_url_rule(
    "/<int:card_id>/deposit", view_func=DepositView.as_view("card_deposit")
)
bp.add_url_rule(
    "/<int:card_id>/balance", view_func=BalanceView.as_view("card_balance")
)
