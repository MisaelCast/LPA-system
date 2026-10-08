"""capa requiere_celula auditoria dia_semana

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-10-07 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Indica si las auditorías de la capa se ejecutan por célula.
    op.execute(
        "ALTER TABLE capa ADD COLUMN IF NOT EXISTS requiere_celula "
        "BOOLEAN NOT NULL DEFAULT TRUE"
    )
    # Día de la semana en que se habilita la auditoría (0=Lunes..6=Domingo).
    op.execute(
        "ALTER TABLE auditoria ADD COLUMN IF NOT EXISTS dia_semana INTEGER"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE auditoria DROP COLUMN IF EXISTS dia_semana")
    op.execute("ALTER TABLE capa DROP COLUMN IF EXISTS requiere_celula")