"""add code to bank_entities

Revision ID: 4d46878d879d
Revises: 0694ce25a6ce
Create Date: 2026-03-29 12:32:14.244006

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4d46878d879d"
down_revision: Union[str, Sequence[str], None] = "0694ce25a6ce"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM bank_entities;")
    op.add_column("bank_entities", sa.Column("code", sa.String(4), nullable=False))


def downgrade() -> None:
    op.drop_column("bank_entities", "code")
