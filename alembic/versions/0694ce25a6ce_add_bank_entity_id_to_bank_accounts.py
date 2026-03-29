"""add bank_entity_id to bank_accounts

Revision ID: 0694ce25a6ce
Revises: xxxx_bank_entities
Create Date: 2026-03-29 11:46:59.463391

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0694ce25a6ce"
down_revision: Union[str, Sequence[str], None] = "xxxx_bank_entities"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Agregar columna bank_entity_id (nullable por compatibilidad)
    op.add_column(
        "bank_accounts", sa.Column("bank_entity_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "fk_bank_accounts_bank_entity",
        "bank_accounts",
        "bank_entities",
        ["bank_entity_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint(
        "fk_bank_accounts_bank_entity", "bank_accounts", type_="foreignkey"
    )
    op.drop_column("bank_accounts", "bank_entity_id")
