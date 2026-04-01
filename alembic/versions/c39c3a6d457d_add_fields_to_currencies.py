"""add fields to currencies

Revision ID: c39c3a6d457d
Revises: 13e4a15f4c31
Create Date: 2026-04-01 11:08:20.854483

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c39c3a6d457d'
down_revision: Union[str, Sequence[str], None] = '13e4a15f4c31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Agregar columnas
    op.add_column('currencies', sa.Column(
        'flag', sa.String(length=5), nullable=True))
    op.add_column('currencies', sa.Column(
        'decimals', sa.Integer(), nullable=False, server_default='2'))
    op.add_column('currencies', sa.Column(
        'exchange_rate_to_base',
        sa.Numeric(precision=18, scale=6),
        nullable=True
    ))

    # 2. Completar datos del seed anterior
    op.execute("""
        UPDATE currencies SET flag = '🇵🇪', exchange_rate_to_base = 1.0 WHERE code = 'PEN';
        UPDATE currencies SET flag = '🇺🇸', exchange_rate_to_base = 3.75 WHERE code = 'USD';
        UPDATE currencies SET flag = '🇪🇺', exchange_rate_to_base = 4.10 WHERE code = 'EUR';
    """)

    # fallback por seguridad
    op.execute("""
        UPDATE currencies
        SET flag = '🏳️', exchange_rate_to_base = 1.0
        WHERE flag IS NULL;
    """)

    # 3. (opcional pero recomendado) hacer flag NOT NULL
    op.alter_column('currencies', 'flag', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('currencies', 'exchange_rate_to_base')
    op.drop_column('currencies', 'decimals')
    op.drop_column('currencies', 'flag')
