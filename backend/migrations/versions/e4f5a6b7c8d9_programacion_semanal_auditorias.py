"""programacion semanal de auditorias ordenadas por sorteo

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-10-14 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e4f5a6b7c8d9'
down_revision: Union[str, None] = 'd3e4f5a6b7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Marca las auditorías cuyo día de la semana se sortea cada semana.
    op.execute(
        "ALTER TABLE auditoria ADD COLUMN IF NOT EXISTS programacion_semanal "
        "BOOLEAN NOT NULL DEFAULT FALSE"
    )

    # Calendario semanal: una auditoría por día hábil (0=Lunes..4=Viernes).
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS programacion_semanal (
            id SERIAL PRIMARY KEY,
            semana_inicio DATE NOT NULL,
            dia_semana INTEGER NOT NULL CHECK (dia_semana BETWEEN 0 AND 4),
            auditoria_id INTEGER NOT NULL REFERENCES auditoria(id),
            CONSTRAINT uq_programacion_semanal_semana_dia
                UNIQUE (semana_inicio, dia_semana)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_programacion_semanal_semana_inicio "
        "ON programacion_semanal (semana_inicio)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_programacion_semanal_semana_inicio")
    op.execute("DROP TABLE IF EXISTS programacion_semanal")
    op.execute(
        "ALTER TABLE auditoria DROP COLUMN IF EXISTS programacion_semanal"
    )
