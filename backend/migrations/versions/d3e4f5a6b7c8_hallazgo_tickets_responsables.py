"""hallazgo tickets y responsables de manufactura

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-10-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd3e4f5a6b7c8'
down_revision: Union[str, None] = 'c2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fecha límite del ticket (para detectar atrasos).
    op.execute(
        "ALTER TABLE hallazgo ADD COLUMN IF NOT EXISTS fecha_limite TIMESTAMP"
    )

    # Historial de seguimiento: una fila por cada actualización (inmutable).
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS hallazgo_seguimiento (
            id SERIAL PRIMARY KEY,
            hallazgo_id INTEGER NOT NULL REFERENCES hallazgo(id),
            usuario_id INTEGER NOT NULL REFERENCES usuario(id),
            tipo VARCHAR(30) NOT NULL,
            detalle VARCHAR(1000),
            estado_desde VARCHAR(20),
            estado_hasta VARCHAR(20),
            fecha_creacion TIMESTAMP NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_hallazgo_seguimiento_hallazgo_id "
        "ON hallazgo_seguimiento (hallazgo_id)"
    )

    # Distingue evidencia del hallazgo original vs. de corrección.
    op.execute(
        "ALTER TABLE evidencia ADD COLUMN IF NOT EXISTS tipo "
        "VARCHAR(20) NOT NULL DEFAULT 'original'"
    )

    # Renombra el estado en desuso en_proceso -> en_correccion.
    op.execute(
        "UPDATE hallazgo SET estado = 'en_correccion' "
        "WHERE estado = 'en_proceso'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE hallazgo SET estado = 'en_proceso' "
        "WHERE estado = 'en_correccion'"
    )
    op.execute("ALTER TABLE evidencia DROP COLUMN IF EXISTS tipo")
    op.execute("DROP INDEX IF EXISTS ix_hallazgo_seguimiento_hallazgo_id")
    op.execute("DROP TABLE IF EXISTS hallazgo_seguimiento")
    op.execute("ALTER TABLE hallazgo DROP COLUMN IF EXISTS fecha_limite")
