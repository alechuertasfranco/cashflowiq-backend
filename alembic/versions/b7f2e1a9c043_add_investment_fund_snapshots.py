"""add investment_fund_snapshots

Revision ID: b7f2e1a9c043
Revises: a1b2c3d4e5f6
Create Date: 2026-06-09 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7f2e1a9c043'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "investment_fund_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("investment_fund_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("value", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.ForeignKeyConstraint(
            ["investment_fund_id"], ["investment_funds.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "investment_fund_id", "snapshot_date",
            name="uq_investment_fund_snapshots_fund_date",
        ),
    )
    op.create_index(
        "ix_investment_fund_snapshots_id",
        "investment_fund_snapshots",
        ["id"],
    )
    op.create_index(
        "ix_investment_fund_snapshots_investment_fund_id",
        "investment_fund_snapshots",
        ["investment_fund_id"],
    )
    op.create_index(
        "ix_investment_fund_snapshots_user_id",
        "investment_fund_snapshots",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_investment_fund_snapshots_user_id",
        table_name="investment_fund_snapshots",
    )
    op.drop_index(
        "ix_investment_fund_snapshots_investment_fund_id",
        table_name="investment_fund_snapshots",
    )
    op.drop_index(
        "ix_investment_fund_snapshots_id",
        table_name="investment_fund_snapshots",
    )
    op.drop_table("investment_fund_snapshots")
