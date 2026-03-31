"""add currencies and refactor bank_accounts

Revision ID: 13e4a15f4c31
Revises: 9636e4f13bba
Create Date: 2026-03-31 12:06:24.665535

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "13e4a15f4c31"
down_revision: Union[str, Sequence[str], None] = "9636e4f13bba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Crear tabla currencies
    op.create_table(
        "currencies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=3), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("symbol", sa.String(length=5), nullable=False),
        sa.UniqueConstraint("code"),
    )

    # 2. Seed básico (clave para no romper FK)
    op.bulk_insert(
        sa.table(
            "currencies",
            sa.column("id", sa.Integer),
            sa.column("code", sa.String),
            sa.column("name", sa.String),
            sa.column("symbol", sa.String),
        ),
        [
            {"id": 1, "code": "PEN", "name": "Sol", "symbol": "S/"},
            {"id": 2, "code": "USD", "name": "Dollar", "symbol": "$"},
            {"id": 3, "code": "EUR", "name": "Euro", "symbol": "€"},
        ],
    )

    # 3. Crear columna temporal INTEGER
    op.add_column(
        "bank_accounts", sa.Column(
            "currency_id_tmp", sa.Integer(), nullable=True)
    )

    # 4. Mapear valores STRING → FK
    op.execute(
        """
        UPDATE bank_accounts
        SET currency_id_tmp = c.id
        FROM currencies c
        WHERE bank_accounts.currency_id = c.code
    """
    )

    # ⚠️ fallback por si hay datos inválidos
    op.execute(
        """
        UPDATE bank_accounts
        SET currency_id_tmp = 1
        WHERE currency_id_tmp IS NULL
    """
    )

    # 5. Eliminar columna vieja
    op.drop_column("bank_accounts", "currency_id")

    # 6. Renombrar columna nueva
    op.alter_column("bank_accounts", "currency_id_tmp",
                    new_column_name="currency_id")

    # 7. Hacerla NOT NULL
    op.alter_column("bank_accounts", "currency_id", nullable=False)

    # 8. Crear FK
    op.create_foreign_key(
        "fk_bank_accounts_currency",
        "bank_accounts",
        "currencies",
        ["currency_id"],
        ["id"],
    )


def downgrade() -> None:
    # 1. Quitar FK
    op.drop_constraint("fk_bank_accounts_currency",
                       "bank_accounts", type_="foreignkey")

    # 2. Volver a string
    op.add_column(
        "bank_accounts", sa.Column("currency_tmp", sa.String(), nullable=True)
    )

    # 3. Mapear FK → code
    op.execute(
        """
        UPDATE bank_accounts
        SET currency_tmp = c.code
        FROM currencies c
        WHERE bank_accounts.currency_id = c.id
    """
    )

    # 4. Eliminar FK column
    op.drop_column("bank_accounts", "currency_id")

    # 5. Renombrar
    op.alter_column("bank_accounts", "currency_tmp",
                    new_column_name="currency_id")

    # 6. NOT NULL
    op.alter_column("bank_accounts", "currency_id", nullable=False)

    # 7. Eliminar tabla currencies
    op.drop_table("currencies")
