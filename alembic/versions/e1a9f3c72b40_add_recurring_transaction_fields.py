"""add recurring transaction fields and recurring_transaction_id to transactions

Revision ID: e1a9f3c72b40
Revises: 2fc7815ef11b
Create Date: 2026-06-06 00:00:00.000000

Adds to recurring_transactions:
  - is_active   Boolean NOT NULL DEFAULT TRUE
  - end_date    Date    NULLABLE
  - currency_id Integer NULLABLE FK -> currencies.id

Adds to transactions:
  - recurring_transaction_id  Integer NULLABLE FK -> recurring_transactions.id
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e1a9f3c72b40"
down_revision: Union[str, Sequence[str], None] = "2fc7815ef11b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- recurring_transactions -------------------------------------------------
    op.add_column(
        "recurring_transactions",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "recurring_transactions",
        sa.Column("end_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "recurring_transactions",
        sa.Column("currency_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_recurring_transactions_currency_id",
        "recurring_transactions",
        "currencies",
        ["currency_id"],
        ["id"],
    )
    op.create_index(
        "ix_recurring_transactions_is_active",
        "recurring_transactions",
        ["is_active"],
    )
    op.create_index(
        "ix_recurring_transactions_next_execution_date",
        "recurring_transactions",
        ["next_execution_date"],
    )

    # --- transactions -----------------------------------------------------------
    op.add_column(
        "transactions",
        sa.Column("recurring_transaction_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_transactions_recurring_transaction_id",
        "transactions",
        "recurring_transactions",
        ["recurring_transaction_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_transactions_recurring_transaction_id"),
        "transactions",
        ["recurring_transaction_id"],
        unique=False,
    )


def downgrade() -> None:
    # --- transactions -----------------------------------------------------------
    op.drop_index(
        op.f("ix_transactions_recurring_transaction_id"),
        table_name="transactions",
    )
    op.drop_constraint(
        "fk_transactions_recurring_transaction_id",
        "transactions",
        type_="foreignkey",
    )
    op.drop_column("transactions", "recurring_transaction_id")

    # --- recurring_transactions -------------------------------------------------
    op.drop_index(
        "ix_recurring_transactions_next_execution_date",
        table_name="recurring_transactions",
    )
    op.drop_index(
        "ix_recurring_transactions_is_active",
        table_name="recurring_transactions",
    )
    op.drop_constraint(
        "fk_recurring_transactions_currency_id",
        "recurring_transactions",
        type_="foreignkey",
    )
    op.drop_column("recurring_transactions", "currency_id")
    op.drop_column("recurring_transactions", "end_date")
    op.drop_column("recurring_transactions", "is_active")
