from flask import jsonify, request, current_app, g
from sqlalchemy import func
from app.api import bp
from app.api.auth import token_auth
from app.models import Movie, Interaction


TOP_POPULAR_PER_PAGE_MIN = 10
TOP_POPULAR_PER_PAGE_MAX = 100
WATCHED_PER_PAGE_MIN = 10
WATCHED_PER_PAGE_MAX = 100
RECOMMENDED_PER_PAGE_MIN = 10
RECOMMENDED_PER_PAGE_MAX = 100


@bp.route('/movie/toppop', methods=['GET'])
@token_auth.login_required
def get_top_popular(id):
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', TOP_POPULAR_PER_PAGE_MIN, type=int), TOP_POPULAR_PER_PAGE_MAX)
    q = Movie.query.order_by(func.cont(Movie.spectators).desc())
    data = Movie.to_collection_dict(q, page, per_page, 'api.get_top_popular')
    return jsonify(data)


@bp.route('/movie/<int:id>/watched', methods=['GET'])
@token_auth.login_required
def get_watched_movies(id):
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', WATCHED_PER_PAGE_MIN, type=int), WATCHED_PER_PAGE_MAX)
    user = g.current_user
    q = Movie.query\
        .join(Interaction.query.filter(Interaction.user_id == user.id, Interaction.score == Interaction.IMPLICIT_RATE),
              Movie.movie_id == Interaction.movie_id)
    data = Movie.to_collection_dict(q, page, per_page, 'api.get_users')
    return jsonify(data)


@bp.route('/movie/<int:id>/recommended', methods=['GET'])
@token_auth.login_required
def get_recommended_movies(id):
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', RECOMMENDED_PER_PAGE_MIN, type=int), RECOMMENDED_PER_PAGE_MAX)
    data = Movie.to_collection_dict(Movie.query, page, per_page, 'api.get_users')  # TODO: setup recommendation
    return jsonify(data)


@bp.route('/movie/<int:id>', methods=['GET'])
@token_auth.login_required
def get_movie(id):
    return jsonify(Movie.query().get_or_404(id).to_dict())
