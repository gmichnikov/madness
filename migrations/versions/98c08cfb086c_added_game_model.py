"""Added Game model

Revision ID: 98c08cfb086c
Revises: c20a8e7e706b
Create Date: 2024-01-13 21:07:30.850506

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '98c08cfb086c'
down_revision = 'c20a8e7e706b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('game',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('round_id', sa.Integer(), nullable=False),
    sa.Column('winner_goes_to_game_id', sa.Integer(), nullable=True),
    sa.Column('team1_id', sa.Integer(), nullable=True),
    sa.Column('team2_id', sa.Integer(), nullable=True),
    sa.Column('winning_team_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['round_id'], ['round.id'], ),
    sa.ForeignKeyConstraint(['team1_id'], ['team.id'], ),
    sa.ForeignKeyConstraint(['team2_id'], ['team.id'], ),
    sa.ForeignKeyConstraint(['winner_goes_to_game_id'], ['game.id'], ),
    sa.ForeignKeyConstraint(['winning_team_id'], ['team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('game')
    # ### end Alembic commands ###
