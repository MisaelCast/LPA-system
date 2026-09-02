"""celula reemplaza nombre y descripcion por numero

Revision ID: 77d7424ea64a
Revises: 43e68b1dc730
Create Date: 2026-09-01 18:27:26.494413

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77d7424ea64a'
down_revision: Union[str, None] = '43e68b1dc730'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Railway tiene una versión antigua de ``celula`` con las columnas
    # ``nombre`` y ``descripcion`` (y 0 registros). El modelo actual usa
    # ``numero`` con una restricción UNIQUE(area_id, numero).
    #
    # Se usa ``IF EXISTS`` / ``IF NOT EXISTS`` para que esta migración sea
    # segura tanto en Railway (donde ``nombre``/``descripcion`` existen) como
    # en un entorno nuevo (donde la migración inicial ya creó ``numero``).
    op.execute("ALTER TABLE celula DROP COLUMN IF EXISTS nombre")
    op.execute("ALTER TABLE celula DROP COLUMN IF EXISTS descripcion")

    # ``numero`` es NOT NULL; como ``celula`` está vacía en Railway, se puede
    # agregar directamente sin valor por defecto.
    op.execute("ALTER TABLE celula ADD COLUMN IF NOT EXISTS numero INTEGER")
    op.execute("ALTER TABLE celula ALTER COLUMN numero SET NOT NULL")

    op.execute(
        "DO $$"
        "BEGIN"
        "    IF NOT EXISTS ("
        "        SELECT 1 FROM pg_constraint"
        "        WHERE conname = 'celula_area_id_numero_key'"
        "          AND conrelid = 'celula'::regclass"
        "    ) THEN"
        "        ALTER TABLE celula ADD CONSTRAINT celula_area_id_numero_key"
        "            UNIQUE (area_id, numero);"
        "    END IF;"
        "END $$;"
    )


def downgrade() -> None:
    # Restaura las columnas legacy (solo si la restricción única ya no existe).
    op.execute(
        "ALTER TABLE celula DROP CONSTRAINT IF EXISTS celula_area_id_numero_key"
    )
    op.execute("ALTER TABLE celula DROP COLUMN IF EXISTS numero")
    op.execute(
        "ALTER TABLE celula ADD COLUMN IF NOT EXISTS nombre VARCHAR(255)"
    )
    op.execute(
        "ALTER TABLE celula ADD COLUMN IF NOT EXISTS descripcion VARCHAR(255)"
    )
