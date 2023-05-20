import functools
from flask import Blueprint, jsonify, request, g, redirect, url_for, current_app
from flask.views import MethodView
from app import db
from app.models import Card, Account
from app.card_state import Disabled, Enabled

bp = Blueprint('cards', __name__, url_prefix="/cards")


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


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
            return jsonify({"error": "Card not found"}), 404

        if not card.verify_owner(g.user):
            return jsonify({"error": "Not authorized"}), 403

        return jsonify(card.to_dict()), 200


class EnableCardView(MethodView):
    decorators = [login_required]

    def put(self, card_id):
        card = Card.query.get(card_id)
        if card is None:
            return jsonify({"error": "Card not found"}), 404

        if not card.verify_owner(g.user):
            return jsonify({"error": "Not authorized"}), 403

        if isinstance(card.state, Enabled):
            return jsonify({"error": "The card is already enabled"}), 400

        card.enable()
        db.session.commit()
        
        return jsonify(card.to_dict()), 200


class DisableCardView(MethodView):
    decorators = [login_required]

    def put(self, card_id):
        card = Card.query.get(card_id)
        if card is None:
            return jsonify({"error": "Card not found"}), 404

        if not card.verify_owner(g.user):
            return jsonify({"error": "Not authorized"}), 403

        if isinstance(card.state, Disabled):
            return jsonify({"error": "The card is already disabled"}), 400

        card.disable()
        db.session.commit()
        
        return jsonify(card.to_dict()), 200


class WithdrawView(MethodView):
    decorators = [login_required]

    def post(self, card_id):
        card = Card.query.get(card_id)
        if card is None:
            current_app.logger.error("Card not found")
            return jsonify({"error": "Card not found"}), 404

        if not card.verify_owner(g.user):
            current_app.logger.error("Not authorized")
            return jsonify({"error": "Not authorized"}), 403

        account_id = card.account.id
        account = Account.query.get(account_id)

        if account is None:
            current_app.logger.error("Account not found")
            return jsonify(error='Account not found'), 404

        amount = request.json.get("amount")

        # TODO@Ando: 일정 금액 이상 인출 시, 알림 이용하기. (알림 시스템 구축)
        is_successful, message = card.withdraw(account, amount)
        db.session.commit()

        if is_successful:
            current_app.logger.info(message)
        else:
            current_app.logger.warning(message)

        return (
            jsonify(
                {
                    "message": "Withdrawl successful",
                    "account": card.to_dict(),
                }
            ),
            200,
        )


class DepositView(MethodView):
    decorators = [login_required]

    def post(self, card_id):
        card = Card.query.get(card_id)
        if card is None:
            return jsonify({"error": "Card not found"}), 404

        if not card.verify_owner(g.user):
            return jsonify({"error": "Not authorized"}), 403

        account_id = card.account.id
        account = Account.query.get(account_id)

        if account is None:
            return jsonify(error='Account not found'), 404

        amount = request.json.get("amount")

        # TODO@Ando: 알림 이용하기. (알림 시스템 구축)
        print(card.deposit(account, amount))

        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Deposit successful",
                    "account": card.to_dict(),
                }
            ),
            200,
        )


# TODO@Ando: balance도 카드 상태에 따라 제한을 두는 것은 어때?
class BalanceView(MethodView):
    decorators = [login_required]

    def get(self, card_id):
        card = Card.query.get(card_id)
        if card is None:
            return jsonify({"error": "Card not found"}), 404

        if not card.verify_owner(g.user):
            return jsonify({"error": "Not authorized"}), 403

        return jsonify({"balance": f"{card.account.balance}"}), 200


bp.add_url_rule('/', view_func=CardListView.as_view('card'))
bp.add_url_rule('/<int:card_id>', view_func=CardView.as_view('card_detail'))
bp.add_url_rule('/<int:card_id>/enable', view_func=EnableCardView.as_view('enable_card'))
bp.add_url_rule('/<int:card_id>/disable', view_func=DisableCardView.as_view('disable_card'))
bp.add_url_rule('/<int:card_id>/withdraw', view_func=WithdrawView.as_view('card_withdraw'))
bp.add_url_rule('/<int:card_id>/deposit', view_func=DepositView.as_view('card_deposit'))
bp.add_url_rule('/<int:card_id>/balance', view_func=BalanceView.as_view('card_balance'))
