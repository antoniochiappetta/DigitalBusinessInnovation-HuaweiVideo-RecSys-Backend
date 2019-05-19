from flask import jsonify, url_for, request, g
from app import db
from app.api import bp
from app.api.errors import bad_input
from app.api.auth import token_auth
from app.models import User


@bp.route('/user/<int:id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    if g.current_user.id != id:
        return bad_input("Access denied")
    return jsonify(g.current_user.to_dict())


@bp.route('/user', methods=['POST'])
def create_user():
    data = request.get_json() or {}
    if 'username' not in data or 'email' not in data or 'password' not in data:
        return bad_input('must include at least username, email and password fields')
    if User.query.filter_by(username=data['username']).first():
        return bad_input('please use a different username')
    if User.query.filter_by(email=data['email']).first():
        return bad_input('please use a different email address')
    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    response = jsonify(user.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_user', id=user.id)
    return response


@bp.route('/user/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_user(id):
    if g.current_user.id != id:
        return bad_input("Access denied")
    user = User.query.get_or_404(id)
    data = request.get_json() or {}
    if 'username' in data and data['username'] != user.username and \
            User.query.filter_by(username=data['username']).first():
        return bad_input('please use a different username')
    if 'email' in data and data['email'] != user.email and \
            User.query.filter_by(email=data['email']).first():
        return bad_input('please use a different email address')
    user.from_dict(data, new_user=False)
    db.session.commit()
    return '', 204


@bp.route('/user/<int:id>', methods=['DELETE'])
@token_auth.login_required
def delete_user(id):
    if g.current_user.id != id:
        return bad_input("Access denied")
    User.quey.filter_by(id=id).delete()
    return '', 204
