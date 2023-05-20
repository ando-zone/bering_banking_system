from flask import Blueprint, jsonify

bp = Blueprint('main', __name__, url_prefix='/')

@bp.route('/')
def home():
    return jsonify(message="Welcome to Bering Bank!")