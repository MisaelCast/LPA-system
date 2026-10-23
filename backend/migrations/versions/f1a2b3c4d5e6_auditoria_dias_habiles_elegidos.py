"""dias habiles elegidos por auditoria (recurrencia semanal)

Revision ID: f1a2b3c4d5e6
Revises: e4f5a6b7c8d9
Create Date: 2026-10-22 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'e4f5a6b7c8d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Días hábiles (0=Lunes..4=Viernes) en que la auditoría se ejecuta cada
    # semana, dentro del periodo de su frecuencia. Sin filas = sin recurrencia
    # por días elegidos (comportamiento según frecuencia).
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS auditoria_dia (
            id SERIAL PRIMARY KEY,
            auditoria_id INTEGER NOT NULL REFERENCES auditoria(id),
            dia_semana INTEGER NOT NULL CHECK (dia_semana BETWEEN 0 AND 4),
            CONSTRAINT uq_auditoria_dia UNIQUE (auditoria_id, dia_semana)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_auditoria_dia_auditoria_id "
        "ON auditoria_dia (auditoria_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS auditoria_dia")
