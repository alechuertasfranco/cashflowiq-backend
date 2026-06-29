"""add payment_services table

Revision ID: d1e2f3a4b5c6
Revises: c4f7e2b19d38
Branch labels: None
depends_on: None
Create Date: 2026-06-29 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'd1e2f3a4b5c6'
down_revision = 'c4f7e2b19d38'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'payment_services',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('service_type', sa.String(), nullable=False, server_default='generic'),
        sa.Column('account_id', sa.Integer(), nullable=True),
        sa.Column('credit_card_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['account_id'], ['bank_accounts.id']),
        sa.ForeignKeyConstraint(['credit_card_id'], ['credit_cards.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_payment_services_id'), 'payment_services', ['id'], unique=False)
    op.create_index(op.f('ix_payment_services_user_id'), 'payment_services', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_payment_services_user_id'), table_name='payment_services')
    op.drop_index(op.f('ix_payment_services_id'), table_name='payment_services')
    op.drop_table('payment_services')
