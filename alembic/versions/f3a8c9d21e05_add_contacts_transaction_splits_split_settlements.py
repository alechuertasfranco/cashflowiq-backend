"""add contacts, transaction_splits, and split_settlements tables

Revision ID: f3a8c9d21e05
Revises: e1a9f3c72b40
Create Date: 2026-06-06 12:00:00.000000

Adds:
  - contacts table (id, user_id, name, email, phone)
  - transaction_splits table (id, transaction_id, contact_id, amount, is_settled, created_at)
  - split_settlements table (id, split_id, amount, date, transaction_id)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f3a8c9d21e05"
down_revision: Union[str, Sequence[str], None] = "e1a9f3c72b40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- contacts ---------------------------------------------------------------
    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_contacts_id"), "contacts", ["id"], unique=False)
    op.create_index("ix_contacts_user_id", "contacts", ["user_id"], unique=False)

    # --- transaction_splits -----------------------------------------------------
    op.create_table(
        "transaction_splits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column(
            "is_settled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_transaction_splits_id"), "transaction_splits", ["id"], unique=False
    )
    op.create_index(
        "ix_transaction_splits_transaction_id",
        "transaction_splits",
        ["transaction_id"],
        unique=False,
    )
    op.create_index(
        "ix_transaction_splits_contact_id",
        "transaction_splits",
        ["contact_id"],
        unique=False,
    )

    # --- split_settlements ------------------------------------------------------
    op.create_table(
        "split_settlements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("split_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column(
            "date",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("transaction_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["split_id"], ["transaction_splits.id"]),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_split_settlements_id"), "split_settlements", ["id"], unique=False
    )
    op.create_index(
        "ix_split_settlements_split_id",
        "split_settlements",
        ["split_id"],
        unique=False,
    )


def downgrade() -> None:
    # --- split_settlements ------------------------------------------------------
    op.drop_index("ix_split_settlements_split_id", table_name="split_settlements")
    op.drop_index(op.f("ix_split_settlements_id"), table_name="split_settlements")
    op.drop_table("split_settlements")

    # --- transaction_splits -----------------------------------------------------
    op.drop_index(
        "ix_transaction_splits_contact_id", table_name="transaction_splits"
    )
    op.drop_index(
        "ix_transaction_splits_transaction_id", table_name="transaction_splits"
    )
    op.drop_index(
        op.f("ix_transaction_splits_id"), table_name="transaction_splits"
    )
    op.drop_table("transaction_splits")

    # --- contacts ---------------------------------------------------------------
    op.drop_index("ix_contacts_user_id", table_name="contacts")
    op.drop_index(op.f("ix_contacts_id"), table_name="contacts")
    op.drop_table("contacts")
