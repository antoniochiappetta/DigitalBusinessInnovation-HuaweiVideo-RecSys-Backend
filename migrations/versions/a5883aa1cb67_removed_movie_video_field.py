"""removed movie video field

Revision ID: a5883aa1cb67
Revises: 94dbe700b3cd
Create Date: 2019-05-25 19:52:16.392217

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'a5883aa1cb67'
down_revision = '94dbe700b3cd'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('movie') as batch_op:
        batch_op.drop_column('video')


def downgrade():
    with op.batch_alter_table('movie') as batch_op:
        batch_op.drop_column('ytbe_id')
