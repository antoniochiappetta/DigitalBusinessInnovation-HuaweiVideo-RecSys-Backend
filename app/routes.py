from app import app
from flask import make_response, jsonify


@app.route('/')
def index():
    return "Hello, World!"  # TODO: add api version list


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 400)
