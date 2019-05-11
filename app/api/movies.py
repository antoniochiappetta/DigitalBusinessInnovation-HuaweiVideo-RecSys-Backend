from app.api import bp


@bp.route('/movie/<int:id>/watched', methods=['GET'])
def get_watched_movies(id):
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(User.query, page, per_page, 'api.get_users')
    return jsonify(data)
    pass

@bp.route('/movie/<int:id>/recommended', methods=['GET'])
def get_recommended_movies(id):
    pass

@bp.route('/movie/<int:id>', methods=['GET'])
def get_movie(id):
    pass
