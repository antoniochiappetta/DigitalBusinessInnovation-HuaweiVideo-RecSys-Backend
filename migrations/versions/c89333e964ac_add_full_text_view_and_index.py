"""add full text view and index

Revision ID: c89333e964ac
Revises: a5883aa1cb67
Create Date: 2019-05-26 11:50:14.852552

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c89333e964ac'
down_revision = 'a5883aa1cb67'
branch_labels = None
depends_on = None


trigger_tuples = [
    ('movie', 'title'),
    ('movie', 'description'),
]


index_set = [
    'tsv_movie_title',
    'tsv_movie_description',
]


def upgrade():
    # grab a connection to the database
    conn = op.get_bind()

    # create the materialized view
    conn.execute(sa.sql.text('''
        CREATE MATERIALIZED VIEW search_view AS (
            SELECT movie.id as id,
                   movie.title as title,
                   setweight(to_tsvector('english', movie.title), 'A') ||
                   setweight(to_tsvector('english', coalesce(movie.description)), 'B') as document
            FROM movie
        )
    '''))

    # create unique index on ids
    op.create_index(op.f('ix_search_view_id'), 'search_view', ['id'], unique=True)

    # create remaining indices on the tsv columns
    op.create_index(op.f('ix_tsv_document'), 'search_view', ['document'], postgresql_using='gin')

    # for triggers, we need to build a new function which runs our refresh materialized view
    conn.execute(sa.sql.text('''
        CREATE OR REPLACE FUNCTION trig_refresh_search_view() RETURNS trigger AS
        $$
        BEGIN
            REFRESH MATERIALIZED VIEW CONCURRENTLY search_view;
            RETURN NULL;
        END;
        $$
        LANGUAGE plpgsql ;
    '''))
    for table, column in trigger_tuples:
        conn.execute(sa.sql.text('''
            DROP TRIGGER IF EXISTS tsv_{table}_{column}_trigger ON {table}
        '''.format(table=table, column=column)))
        conn.execute(sa.sql.text('''
            CREATE TRIGGER tsv_{table}_{column}_trigger AFTER TRUNCATE OR INSERT OR DELETE OR UPDATE OF {column}
            ON {table} FOR EACH STATEMENT
            EXECUTE PROCEDURE trig_refresh_search_view()
        '''.format(table=table, column=column)))

    # mispelling
    # TODO: already in heroku ps, check whether already existing else:
    #       conn.execute(sa.sql.text('CREATE EXTENSION pg_trgm;'))

    # unique lexeme view
    conn.execute(sa.sql.text('''
        CREATE MATERIALIZED VIEW unique_lexeme AS
            SELECT word FROM ts_stat(
            'SELECT to_tsvector(''simple'', title) || 
                    to_tsvector(''simple'', description)
            FROM movie');
    '''))

    # CREATE INDEX words_idx ON search_words USING gin(word gin_trgm_ops);
    op.create_index(op.f('ix_unique_lexeme'), 'unique_lexeme', ['word'], postgresql_using='GIN',
                    postgresql_ops={"word": "gin_trgm_ops"})
    conn.execute('REFRESH MATERIALIZED VIEW unique_lexeme;')


def downgrade():
    # grab a connection to the database
    conn = op.get_bind()

    # drop the materialized view
    conn.execute(sa.sql.text('DROP MATERIALIZED VIEW search_view'))

    for table, column, _ in trigger_tuples:
        conn.execute(sa.sql.text('''
            DROP TRIGGER IF EXISTS tsv_{table}_{column}_trigger ON {table}
        '''.format(table=table, column=column)))

    # mispelling
    conn.execute(sa.sql.text('DROP MATERIALIZED VIEW unique_lexeme'))
    # conn.execute(sa.sql.text('DROP EXTENSION pg_trgm;'))
