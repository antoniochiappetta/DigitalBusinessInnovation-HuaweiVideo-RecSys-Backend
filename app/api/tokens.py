from flask import g, jsonify
from app import db
from app.api import bp
from app.api.auth import basic_auth, token_auth


@bp.route('/token', methods=['POST'])
@basic_auth.login_required
def get_token():
    token = g.current_user.get_token(expires_in=2592000)  # expires in one month
    db.session.commit()
    return jsonify({'token': token, 'sub': g.current_user.id})


@bp.route('/token', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    g.current_user.revoke_token()
    db.session.commit()
    return '', 204
