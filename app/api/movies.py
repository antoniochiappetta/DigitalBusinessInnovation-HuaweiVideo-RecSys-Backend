from app.api import bp


@bp.route('/movie/<int:id>/watched', methods=['GET'])
def get_watched_movies(id):
    pass

@bp.route('/movie/<int:id>/recommended', methods=['GET'])
def get_recommended_movies(id):
    pass

@bp.route('/movie/<int:id>', methods=['GET'])
def get_movie(id):
    pass
