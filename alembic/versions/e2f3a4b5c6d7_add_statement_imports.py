"""add statement_imports table + transactions.import_batch_id

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Branch labels: None
depends_on: None
Create Date: 2026-07-23 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'e2f3a4b5c6d7'
down_revision = 'd1e2f3a4b5c6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'statement_imports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('bank', sa.String(), nullable=True),
        sa.Column('imported_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['account_id'], ['bank_accounts.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_statement_imports_id'), 'statement_imports', ['id'], unique=False)
    op.create_index(op.f('ix_statement_imports_user_id'), 'statement_imports', ['user_id'], unique=False)
    op.create_index(op.f('ix_statement_imports_account_id'), 'statement_imports', ['account_id'], unique=False)

    op.add_column('transactions', sa.Column('import_batch_id', sa.Integer(), nullable=True))
    op.create_index(
        op.f('ix_transactions_import_batch_id'), 'transactions', ['import_batch_id'], unique=False
    )
    op.create_foreign_key(
        'fk_transactions_import_batch_id_statement_imports',
        'transactions',
        'statement_imports',
        ['import_batch_id'],
        ['id'],
    )


def downgrade() -> None:
    op.drop_constraint(
        'fk_transactions_import_batch_id_statement_imports', 'transactions', type_='foreignkey'
    )
    op.drop_index(op.f('ix_transactions_import_batch_id'), table_name='transactions')
    op.drop_column('transactions', 'import_batch_id')

    op.drop_index(op.f('ix_statement_imports_account_id'), table_name='statement_imports')
    op.drop_index(op.f('ix_statement_imports_user_id'), table_name='statement_imports')
    op.drop_index(op.f('ix_statement_imports_id'), table_name='statement_imports')
    op.drop_table('statement_imports')
