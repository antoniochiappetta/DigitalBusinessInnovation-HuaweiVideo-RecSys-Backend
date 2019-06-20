from flask import jsonify, request, g
from sqlalchemy import func
from flask_sqlalchemy import Pagination
from app.api import bp
from app.api.auth import token_auth
from app.models import Movie, Interaction, Recommendation
from app.searches import search_movie


TOP_POPULAR_PER_PAGE_MIN = 10
TOP_POPULAR_PER_PAGE_MAX = 100
WATCHED_PER_PAGE_MIN = 10
WATCHED_PER_PAGE_MAX = 100
RECOMMENDED_PER_PAGE_MIN = 10
RECOMMENDED_PER_PAGE_MAX = 100


@bp.route('/movie/toppop', methods=['GET'])
@token_auth.login_required
def get_top_popular():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', TOP_POPULAR_PER_PAGE_MIN, type=int), TOP_POPULAR_PER_PAGE_MAX)
    q = Movie.query\
        .join(Interaction)\
        .group_by(Movie.id)\
        .order_by(func.count(Interaction.user_id).desc())
    data = Movie.to_collection_dict(q, page, per_page, 'api.get_top_popular')
    return jsonify(data)


@bp.route('/movie/watched/<int:id>', methods=['GET'])
@token_auth.login_required
def get_watched_movies(id):
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', WATCHED_PER_PAGE_MIN, type=int), WATCHED_PER_PAGE_MAX)
    user = g.current_user
    q = Movie.query\
        .join(Interaction)\
        .filter(Interaction.user_id == user.id, Interaction.score == Interaction.IMPLICIT_RATE)\
        .order_by(Interaction.timestamp.desc())
    data = Movie.to_collection_dict(q, page, per_page, 'api.get_watched_movies', id=user.id)
    return jsonify(data)


@bp.route('/movie/recommended/<int:id>', methods=['GET'])
@token_auth.login_required
def get_recommended_movies(id):
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', RECOMMENDED_PER_PAGE_MIN, type=int), RECOMMENDED_PER_PAGE_MAX)
    user = g.current_user
    q = Movie.query\
        .join(Recommendation, Recommendation.movie_id == Movie.id)\
        .filter(Recommendation.user_id == user.id)\
        .order_by(Recommendation.rank)
    data = Movie.to_collection_dict(q, page, per_page, 'api.get_recommended_movies', id=user.id)
    return jsonify(data)


@bp.route('/movie/<int:id>', methods=['GET'])
@token_auth.login_required
def get_movie(id):
    return jsonify(Movie.query.get_or_404(id, description='Movie not found').to_dict())


@bp.route('/movie/searchByKeywords', methods=['GET'])
@token_auth.login_required
def get_search_by_keywords():
    q = request.args.get('q', '', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', RECOMMENDED_PER_PAGE_MIN, type=int), RECOMMENDED_PER_PAGE_MAX)

    movies_pagination = search_movie(q, per_page=per_page, page=page) if q != ' ' and q != '' \
        else Pagination(None, 1, 0, 0, [])

    return jsonify(Movie.get_collection_dict(movies_pagination, 'api.get_search_by_keywords'))
