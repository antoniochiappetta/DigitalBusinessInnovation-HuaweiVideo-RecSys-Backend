from app import db
from sqlalchemy import text


class SearchResult(object):
    def __init__(self, movie_id, title):
        self.movie_id = movie_id
        self.title = title

    def to_dict(self):
        return {
            'movie_id': self.movie_id,
            'title': self.title
        }


def search_movie(search_text):
    sql = text('''
        SELECT id, title
        FROM search_view
        WHERE document @@ to_tsquery('english', '':keywords'')
        ORDER BY ts_rank(document, to_tsquery('english', '':keywords'')) DESC;
    ''')
    sql = sql.bindparams(keywords=search_text)
    result = db.engine.execute(sql)
    movies = [SearchResult(row[0], row[1]) for row in result]
    return movies
