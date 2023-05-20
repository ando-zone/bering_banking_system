from flask import Blueprint, jsonify

bp = Blueprint('main', __name__, url_prefix='/')

@bp.route('/')
def home():
    #return render_template('index.html', question_num=1)
    return jsonify(message="Welcome to Bering Bank!")