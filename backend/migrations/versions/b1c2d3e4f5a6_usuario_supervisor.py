"""usuario_supervisor relacion gerente supervisores

Revision ID: b1c2d3e4f5a6
Revises: a6b7c8d9e0f1
Create Date: 2026-10-07 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'a6b7c8d9e0f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Relación Gerente -> Supervisores a su cargo (N:M, ambas FK a usuario).
    op.execute(
        "CREATE TABLE IF NOT EXISTS usuario_supervisor ("
        " gerente_id INTEGER NOT NULL REFERENCES usuario(id),"
        " supervisor_id INTEGER NOT NULL REFERENCES usuario(id),"
        " PRIMARY KEY (gerente_id, supervisor_id)"
        ")"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS usuario_supervisor")