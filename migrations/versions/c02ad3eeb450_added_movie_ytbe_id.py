"""added movie ytbe_id

Revision ID: c02ad3eeb450
Revises: 777212c48b20
Create Date: 2019-05-25 15:41:31.948224

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c02ad3eeb450'
down_revision = '777212c48b20'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('movie', sa.Column('ytbe_id', sa.String(length=32), nullable=True))


def downgrade():
    op.add_column('movie', sa.Column('video', sa.VARCHAR(length=64), nullable=True))
