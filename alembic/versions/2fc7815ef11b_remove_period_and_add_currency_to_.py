"""remove period and add currency to budget table

Revision ID: 2fc7815ef11b
Revises: a3d33041be19
Create Date: 2026-04-08 12:55:39.170035

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2fc7815ef11b'
down_revision: Union[str, Sequence[str], None] = 'a3d33041be19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('budgets', sa.Column('currency_id', sa.Integer(), nullable=True))
    op.execute('UPDATE budgets SET currency_id = 1')
    op.alter_column('budgets', 'currency_id', nullable=False)
    op.create_unique_constraint('uq_budget_category_user', 'budgets', ['category_id', 'user_id'])
    op.create_foreign_key('fk_budgets_currency_id', 'budgets', 'currencies', ['currency_id'], ['id'])
    op.drop_column('budgets', 'end_date')
    op.drop_column('budgets', 'start_date')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('budgets', sa.Column('start_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=False))
    op.add_column('budgets', sa.Column('end_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=False))
    op.drop_constraint('fk_budgets_currency_id', 'budgets', type_='foreignkey')
    op.drop_constraint('uq_budget_category_user', 'budgets', type_='unique')
    op.drop_column('budgets', 'currency_id')
    # ### end Alembic commands ###
