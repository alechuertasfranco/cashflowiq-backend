"""add notification_days_before and nullable amount to recurring_transactions

Revision ID: c4f7e2b19d38
Revises: b7f2e1a9c043
Create Date: 2026-06-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'c4f7e2b19d38'
down_revision = 'b7f2e1a9c043'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('recurring_transactions', 'amount', nullable=True)
    op.add_column(
        'recurring_transactions',
        sa.Column('notification_days_before', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('recurring_transactions', 'notification_days_before')
    op.alter_column('recurring_transactions', 'amount', nullable=False)
