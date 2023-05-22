from flask import Blueprint, jsonify, current_app

bp = Blueprint('main', __name__, url_prefix='/')

@bp.route('/')
def home():
    """Bering Bank의 홈 페이지를 렌더링함.

    Returns:
        환영 메시지와 URL 목록을 포함하는 JSON 응답.

    Example:
        {
            "message": "Bering Bank에 오신 것을 환영합니다!",
            "urls": [
                {
                    "url": "/",
                    "endpoint": "home"
                },
                {
                    "url": "/accounts",
                    "endpoint": "accounts"
                },
                ...
            ]
        }
    """
    urls = []
    for rule in current_app.url_map.iter_rules():
        if rule.endpoint != 'static':
            url = {
                'url': rule.rule,
                'endpoint': rule.endpoint
            }
            urls.append(url)

    return jsonify(message="Welcome to Bering Bank!", urls=urls)

