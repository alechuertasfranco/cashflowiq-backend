"""create bank_entities table

Revision ID: 9ba6b7639c88
Revises: xxxx_bank_accounts
Create Date: 2026-03-29 10:50:29.810401

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "xxxx_bank_entities"
down_revision = "xxxx_bank_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 🆕 Crear tabla bank_entities
    op.create_table(
        "bank_entities",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("color", sa.String(6), nullable=True),
    )

    op.create_index(op.f("ix_bank_entities_id"), "bank_entities", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_bank_entities_id"), table_name="bank_entities")
    op.drop_table("bank_entities")
