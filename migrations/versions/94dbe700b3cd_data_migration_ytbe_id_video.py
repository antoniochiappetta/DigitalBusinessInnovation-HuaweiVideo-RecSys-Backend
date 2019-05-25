"""data migration ytbe_id / video

Revision ID: 94dbe700b3cd
Revises: c02ad3eeb450
Create Date: 2019-05-25 19:49:13.505413

"""
from alembic import op
from sqlalchemy.orm.session import Session
from app import db
from app.models import Movie
from urllib.parse import urlparse, parse_qs


# revision identifiers, used by Alembic.
revision = '94dbe700b3cd'
down_revision = 'c02ad3eeb450'
branch_labels = None
depends_on = None


def get_youtube_id(url):
    u_pars = urlparse(url)
    query_v = parse_qs(u_pars.query).get('v')
    if query_v:
        return query_v[0]
    pth = u_pars.path.split('/')
    if pth:
        return pth[-1]


class MovieMid(Movie):
    video = db.Column(db.String(64))


def upgrade():
    session = Session(bind=op.get_bind())
    for movie in session.query(MovieMid):
        movie.ytbe_id = get_youtube_id(movie.video)
    session.commit()


def downgrade():
    session = Session(bind=op.get_bind())
    for movie in session.query(Movie):
        movie.video = 'https://www.youtube.com/watch?v=' + movie.ytbe_id
    session.commit()
