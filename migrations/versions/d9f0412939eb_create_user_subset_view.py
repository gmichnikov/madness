"""Create user_subset view

Revision ID: d9f0412939eb
Revises: 33cfc0ad6a92
Create Date: 2024-01-27 10:30:25.665258

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd9f0412939eb'
down_revision = '33cfc0ad6a92'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE VIEW user_subset AS SELECT id, email, full_name, is_admin, is_verified, is_bracket_valid, pool_id from public.user;")


def downgrade():
    op.execute("DROP VIEW user_subset")
