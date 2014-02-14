"""Removidas as classes Ticket e Comment

Revision ID: 488ce739fedd
Revises: a8e066255c5
Create Date: 2014-02-10 17:04:57.263783

"""

# revision identifiers, used by Alembic.
revision = '488ce739fedd'
down_revision = 'a8e066255c5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_table('comment')
    op.drop_table('ticket')


def downgrade():
    op.create_table(
        'ticket',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('is_open', sa.Boolean),
        sa.Column('started_at', sa.DateTime, nullable=False),
        sa.Column('finished_at', sa.DateTime),
        sa.Column('articlepkg_id', sa.Integer, sa.ForeignKey('articlepkg.id')),
        sa.Column('title', sa.String, nullable=False),
        sa.Column('author', sa.String, nullable=False)
    )

    op.create_table(
        'comment',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('date', sa.DateTime, nullable=False),
        sa.Column('author', sa.String, nullable=False),
        sa.Column('message', sa.String, nullable=False),
        sa.Column('ticket_id', sa.Integer, sa.ForeignKey('ticket.id'))
    )

