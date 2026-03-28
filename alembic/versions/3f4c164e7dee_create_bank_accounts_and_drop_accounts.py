# alembic/versions/xxxx_create_bank_accounts_and_drop_accounts.py

"""create bank_accounts and drop accounts

Revision ID: xxxx_bank_accounts
Revises: b90f1dab14c5
Create Date: 2026-03-28

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "xxxx_bank_accounts"
down_revision: Union[str, Sequence[str], None] = "b90f1dab14c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 🆕 Crear nueva tabla correcta
    op.create_table(
        "bank_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "initial_amount", sa.Numeric(12, 2), nullable=False, server_default="0"
        ),
        sa.Column("currency", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_bank_accounts_id"), "bank_accounts", ["id"], unique=False)

    # ❌ eliminar tabla antigua
    op.drop_table("accounts")


def downgrade() -> None:
    # 🔙 recrear tabla antigua
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("balance", sa.Numeric(12, 2), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.drop_index(op.f("ix_bank_accounts_id"), table_name="bank_accounts")
    op.drop_table("bank_accounts")
