from app import db
from app.models import Movie
from sqlalchemy import text
from flask_sqlalchemy import Pagination


def search_movie(search_text, page, per_page):
    sql = text('''
        WITH similar_words AS (
            SELECT string_agg(word, ' ') AS words
            FROM (
                SELECT word
                FROM unique_lexeme
                WHERE word % '':keywords''
                ORDER BY word <-> '':keywords''
                LIMIT 5
            ) AS tab
        )
        SELECT id, count(*) OVER() AS full_count
        FROM search_view
        WHERE document @@ to_tsquery('english', (SELECT words FROM similar_words))
        ORDER BY ts_rank(document, to_tsquery('english', (SELECT words FROM similar_words))) DESC
        LIMIT :per_page
        OFFSET :offset_page
    ''')  # TODO consider in conditionally recounting because should get few items every time
    # TODO if there are only stop words, search them only in title (disable warnings)
    sql = sql.bindparams(keywords=search_text, per_page=per_page, offset_page=((page-1) * per_page))
    result = db.engine.execute(sql).fetchall()
    total_count = result[0][1] if len(result) > 0 else 0
    movies = [Movie.query.get(row[0]) for row in result]
    return Pagination(None, page, per_page, total_count, movies)
