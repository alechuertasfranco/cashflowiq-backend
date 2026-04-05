"""add credit_cards and investment_funds

Revision ID: c9ddea26b1ae
Revises: c39c3a6d457d
Create Date: 2026-04-05 11:38:35.129195

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c9ddea26b1ae"
down_revision: Union[str, Sequence[str], None] = "c39c3a6d457d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 🔹 Crear ENUM explícitamente (mejor control)
    card_brand_enum = sa.Enum(
        "VISA",
        "MASTERCARD",
        "AMEX",
        "DISCOVER",
        "DINERS",
        name="card_brand_enum",
        create_type=False,
    )

    # 🔹 credit_cards
    op.create_table(
        "credit_cards",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("credit_limit", sa.Numeric(12, 2), nullable=False),
        sa.Column("brand", card_brand_enum, nullable=False),
        sa.Column("closing_day", sa.Integer(), nullable=False),
        sa.Column("due_day", sa.Integer(), nullable=False),
        sa.Column("interest_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("currency_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("bank_entity_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["currency_id"], ["currencies.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["bank_entity_id"], ["bank_entities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_credit_cards_user_id", "credit_cards", ["user_id"])
    op.create_index(
        "ix_credit_cards_bank_entity_id", "credit_cards", ["bank_entity_id"]
    )

    # 🔹 investment_funds
    op.create_table(
        "investment_funds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("fund_type", sa.String(length=50), nullable=True),
        sa.Column("invested_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("currency_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("bank_entity_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["currency_id"], ["currencies.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["bank_entity_id"], ["bank_entities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_investment_funds_user_id", "investment_funds", ["user_id"])
    op.create_index(
        "ix_investment_funds_bank_entity_id", "investment_funds", ["bank_entity_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_investment_funds_bank_entity_id", table_name="investment_funds")
    op.drop_index("ix_investment_funds_user_id", table_name="investment_funds")
    op.drop_table("investment_funds")

    op.drop_index("ix_credit_cards_bank_entity_id", table_name="credit_cards")
    op.drop_index("ix_credit_cards_user_id", table_name="credit_cards")
    op.drop_table("credit_cards")

    sa.Enum(name="card_brand_enum").drop(op.get_bind(), checkfirst=True)
