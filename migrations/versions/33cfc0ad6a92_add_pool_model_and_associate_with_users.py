"""Add pool model and associate with users

Revision ID: 33cfc0ad6a92
Revises: 5a83f5bfb2fd
Create Date: 2024-01-27 06:22:01.818526

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '33cfc0ad6a92'
down_revision = '5a83f5bfb2fd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('pool',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pool_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'pool', ['pool_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('pool_id')

    op.drop_table('pool')
    # ### end Alembic commands ###
