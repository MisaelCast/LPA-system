"""auditoria agrega tipo_respuesta

Revision ID: e5f8a1b2c3d4
Revises: b1d4e7f20a35
Create Date: 2026-10-05 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e5f8a1b2c3d4'
down_revision: Union[str, None] = 'b1d4e7f20a35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Escala de respuestas de la auditoría: ``semaforo`` (V/A/R) por defecto
    # o ``cumplimiento`` (cumple / no_cumple / na) para auditorías de
    # verificación (por ejemplo, la del Supervisor sobre el trabajo del Auditor).
    op.execute(
        "ALTER TABLE auditoria ADD COLUMN IF NOT EXISTS tipo_respuesta "
        "VARCHAR(20) NOT NULL DEFAULT 'semaforo'"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE auditoria DROP COLUMN IF EXISTS tipo_respuesta")
