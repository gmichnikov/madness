"""Add potential winners model

Revision ID: b0cefe7ef2e1
Revises: 2ae2dbede8d0
Create Date: 2024-03-21 00:00:37.413150

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b0cefe7ef2e1'
down_revision = '2ae2dbede8d0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('potential_winner',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('game_id', sa.Integer(), nullable=False),
    sa.Column('potential_winner_ids', sa.String(), nullable=False),
    sa.Column('last_updated', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['game_id'], ['game.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('potential_winner')
    # ### end Alembic commands ###
