"""add current_value to investment_funds

Revision ID: a1b2c3d4e5f6
Revises: f3a8c9d21e05
Create Date: 2026-06-06 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f3a8c9d21e05'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'investment_funds',
        sa.Column('current_value', sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('investment_funds', 'current_value')
