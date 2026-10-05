"""criterio agrega jerarquia seccion subseccion subtitulo

Revision ID: 9c2f1a4b7d01
Revises: 77d7424ea64a
Create Date: 2026-10-03 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '9c2f1a4b7d01'
down_revision: Union[str, None] = '77d7424ea64a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Columnas opcionales para agrupar criterios bajo títulos/subtítulos.
    # Permiten que la interfaz presente encabezados sin repetir la jerarquía
    # dentro de ``descripcion``. No afectan a auditorías existentes (NULL).
    # ``IF NOT EXISTS`` mantiene la migración segura ante esquemas que ya
    # contaban con estas columnas (mismo patrón que la migración de celula).
    op.execute("ALTER TABLE criterio ADD COLUMN IF NOT EXISTS seccion VARCHAR(150)")
    op.execute("ALTER TABLE criterio ADD COLUMN IF NOT EXISTS subseccion VARCHAR(150)")
    op.execute("ALTER TABLE criterio ADD COLUMN IF NOT EXISTS subtitulo VARCHAR(150)")


def downgrade() -> None:
    op.execute("ALTER TABLE criterio DROP COLUMN IF EXISTS subtitulo")
    op.execute("ALTER TABLE criterio DROP COLUMN IF EXISTS subseccion")
    op.execute("ALTER TABLE criterio DROP COLUMN IF EXISTS seccion")
