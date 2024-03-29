"""Added LogEntry model

Revision ID: 6dfcba0b247a
Revises: b584aaf2ab6e
Create Date: 2024-01-13 16:26:44.611592

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6dfcba0b247a'
down_revision = 'b584aaf2ab6e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('log_entry',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('category', sa.String(length=100), nullable=False),
    sa.Column('current_user_id', sa.Integer(), nullable=True),
    sa.Column('description', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['current_user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('log_entry')
    # ### end Alembic commands ###
