from flask import jsonify, request, g, url_for, abort
from app import db
from app.api import bp
from app.api.errors import bad_input, error_response
from app.api.auth import token_auth
from app.models import Movie, Interaction


@bp.route('/interaction', methods=['POST'])
@token_auth.login_required
def create_interaction():
    data = request.get_json() or {}
    for field in ['user_id', 'movie_id']:
        if field not in data:
            return bad_input('must include at least username, email and password fields')

    user = g.current_user
    if user.id != data['user_id']:
        return error_response(403, status="Access denied")

    with db.session.no_autoflush:
        movie = Movie.query.get_or_404(data['movie_id'], description='Movie not found')

        if 'rating' in data:
            if data['rating'] <= 5:
                user.watch_rate(movie, data['rating'])
            else:
                bad_input('Rating must be in between 1 and 5')
        else:
            user.watch(movie)

        db.session.commit()

    response = error_response(status_code=201, status='Created', message='interaction registered')
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_interaction_%s' % ('explicit' if 'rating' in data else 'implicit'),
                                           user_id=user.id, movie_id=movie.id)
    return response


@bp.route('/interaction/<int:user_id>:<int:movie_id>/explicit', methods=['GET'])
@token_auth.login_required
def get_interaction_explicit(user_id, movie_id):
    user = g.current_user
    if user.id != user_id:
        return error_response(403, status="Access denied")

    movie = Movie.query.get(movie_id)
    if movie is None:
        abort(400, description='Movie not found')

    if not user.has_rated(movie):
        return error_response(404, status='Rate not found', message='Rate missing for this movie from this user')

    interaction = Interaction.query.filter_by(user_id=user.id, movie_id=movie.id).first()
    return jsonify(interaction.to_dict(include_ts=True, explicit=True))


@bp.route('/interaction/<int:user_id>:<int:movie_id>/implicit', methods=['GET'])
@token_auth.login_required
def get_interaction_implicit(user_id, movie_id):
    user = g.current_user
    if user.id != user_id:
        return error_response(403, status="Access denied")

    movie = Movie.query.get(movie_id)
    if movie is None:
        abort(400, description='Movie not found')

    if not user.has_watched(movie):
        return error_response(404, status='Implicit rate not found', message='The user has not watched this movie yet')

    interaction = Interaction.query.filter_by(user_id=user.id, movie_id=movie.id).first()
    return jsonify(interaction.to_dict(include_ts=True, explicit=False))
