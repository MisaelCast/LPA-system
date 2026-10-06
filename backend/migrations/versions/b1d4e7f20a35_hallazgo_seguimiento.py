"""hallazgo agrega seguimiento estado accion area responsable fecha cierre

Revision ID: b1d4e7f20a35
Revises: 9c2f1a4b7d01
Create Date: 2026-10-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b1d4e7f20a35'
down_revision: Union[str, None] = '9c2f1a4b7d01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Campos de seguimiento del hallazgo. La descripcion original se conserva.
    op.execute(
        "ALTER TABLE hallazgo ADD COLUMN IF NOT EXISTS estado VARCHAR(20) "
        "NOT NULL DEFAULT 'abierto'"
    )
    op.execute(
        "ALTER TABLE hallazgo ADD COLUMN IF NOT EXISTS accion_correctiva "
        "VARCHAR(1000)"
    )
    op.execute(
        "ALTER TABLE hallazgo ADD COLUMN IF NOT EXISTS area_responsable_id INTEGER"
    )
    op.execute(
        "ALTER TABLE hallazgo ADD COLUMN IF NOT EXISTS fecha_cierre "
        "TIMESTAMP WITH TIME ZONE"
    )

    # FK hacia area .
    op.execute(
        "DO $$"
        "BEGIN"
        "    IF NOT EXISTS ("
        "        SELECT 1 FROM pg_constraint"
        "        WHERE conname = 'hallazgo_area_responsable_id_fkey'"
        "          AND conrelid = 'hallazgo'::regclass"
        "    ) THEN"
        "        ALTER TABLE hallazgo ADD CONSTRAINT"
        "            hallazgo_area_responsable_id_fkey"
        "            FOREIGN KEY (area_responsable_id) REFERENCES area(id);"
        "    END IF;"
        "END $$;"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE hallazgo DROP CONSTRAINT IF EXISTS "
        "hallazgo_area_responsable_id_fkey"
    )
    op.execute("ALTER TABLE hallazgo DROP COLUMN IF EXISTS fecha_cierre")
    op.execute("ALTER TABLE hallazgo DROP COLUMN IF EXISTS area_responsable_id")
    op.execute("ALTER TABLE hallazgo DROP COLUMN IF EXISTS accion_correctiva")
    op.execute("ALTER TABLE hallazgo DROP COLUMN IF EXISTS estado")
