"""programacion auditorias frecuencia dias fecha_programada usuario_celula

Revision ID: a6b7c8d9e0f1
Revises: e5f8a1b2c3d4
Create Date: 2026-10-06 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a6b7c8d9e0f1'
down_revision: Union[str, None] = 'e5f8a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Intervalo en días de la frecuencia (requerido para calendarización).
    op.execute(
        "ALTER TABLE frecuencia ADD COLUMN IF NOT EXISTS dias INTEGER"
    )
    op.execute("UPDATE frecuencia SET dias = 1 WHERE dias IS NULL AND nombre = 'Diaria'")
    op.execute("UPDATE frecuencia SET dias = 7 WHERE dias IS NULL AND nombre = 'Semanal'")
    op.execute("UPDATE frecuencia SET dias = 15 WHERE dias IS NULL AND nombre = 'Quincenal'")
    op.execute("UPDATE frecuencia SET dias = 30 WHERE dias IS NULL AND nombre = 'Mensual'")
    op.execute("UPDATE frecuencia SET dias = 60 WHERE dias IS NULL AND nombre = 'Bimestral'")
    op.execute("UPDATE frecuencia SET dias = 90 WHERE dias IS NULL AND nombre = 'Trimestral'")
    op.execute("UPDATE frecuencia SET dias = 365 WHERE dias IS NULL AND nombre = 'Anual'")
    op.execute("UPDATE frecuencia SET dias = 7 WHERE dias IS NULL")
    op.execute(
        "ALTER TABLE frecuencia ALTER COLUMN dias SET NOT NULL"
    )

    # Fecha programada de la ejecución (inicio del periodo vigente).
    op.execute(
        "ALTER TABLE ejecucion_auditoria ADD COLUMN IF NOT EXISTS "
        "fecha_programada TIMESTAMP WITH TIME ZONE"
    )

    # Asignación de células a cargo de un usuario (N:M).
    op.execute(
        "CREATE TABLE IF NOT EXISTS usuario_celula ("
        " usuario_id INTEGER NOT NULL REFERENCES usuario(id),"
        " celula_id INTEGER NOT NULL REFERENCES celula(id),"
        " PRIMARY KEY (usuario_id, celula_id)"
        ")"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS usuario_celula")
    op.execute(
        "ALTER TABLE ejecucion_auditoria DROP COLUMN IF EXISTS fecha_programada"
    )
    op.execute("ALTER TABLE frecuencia DROP COLUMN IF EXISTS dias")