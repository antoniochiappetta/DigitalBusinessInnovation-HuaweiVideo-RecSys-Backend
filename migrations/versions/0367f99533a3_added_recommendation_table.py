"""added recommendation table

Revision ID: 0367f99533a3
Revises: c89333e964ac
Create Date: 2019-06-20 04:12:01.713843

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0367f99533a3'
down_revision = 'c89333e964ac'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('recommendation',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('movie_id', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('rank', sa.Integer(), nullable=False),
    sa.Column('recommender_name', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id']),
    sa.PrimaryKeyConstraint('user_id', 'rank')
    )
    op.create_index(op.f('ix_recommendation_timestamp'), 'recommendation', ['timestamp'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_recommendation_timestamp'), table_name='recommendation')
    op.drop_table('recommendation')
