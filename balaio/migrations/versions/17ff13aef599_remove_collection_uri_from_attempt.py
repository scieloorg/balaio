"""Remove collection_uri from Attempt

Revision ID: 17ff13aef599
Revises: 1e30ab23b61f
Create Date: 2014-03-06 13:42:48.861240

"""

# revision identifiers, used by Alembic.
revision = '17ff13aef599'
down_revision = '1e30ab23b61f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('attempt', 'collection_uri')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('attempt', sa.Column('collection_uri', sa.VARCHAR(), nullable=True))
    ### end Alembic commands ###