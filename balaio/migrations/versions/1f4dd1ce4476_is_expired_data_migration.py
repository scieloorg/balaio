"""is_expired data migration

Revision ID: 1f4dd1ce4476
Revises: 1f579a087211
Create Date: 2014-06-05 18:46:33.608296

"""

# revision identifiers, used by Alembic.
revision = '1f4dd1ce4476'
down_revision = '1f579a087211'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute('UPDATE attempt SET is_expired = FALSE')


def downgrade():
    pass
