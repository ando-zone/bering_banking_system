from flask import Blueprint, jsonify, current_app

bp = Blueprint('main', __name__, url_prefix='/')

@bp.route('/')
def home():
    urls = []
    for rule in current_app.url_map.iter_rules():
        if rule.endpoint != 'static':
            url = {
                'url': rule.rule,
                'endpoint': rule.endpoint
            }
            urls.append(url)

    return jsonify(message="Welcome to Bering Bank!", urls=urls)

