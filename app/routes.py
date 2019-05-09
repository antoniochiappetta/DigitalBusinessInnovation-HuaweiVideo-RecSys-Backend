from flask import make_response, jsonify, Blueprint


bp = Blueprint('routers', __name__)


@bp.route('/')
def index():
    return "Hello, World!"  # TODO: add api version list


@bp.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 400)
