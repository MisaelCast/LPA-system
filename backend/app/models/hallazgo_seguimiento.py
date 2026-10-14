from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.hallazgo import Hallazgo
    from app.models.usuario import Usuario


TIPOS_SEGUIMIENTO = (
    "asignacion",
    "comentario",
    "accion_correctiva",
    "estado",
    "solicitud_cierre",
    "cierre_aprobado",
    "cierre_rechazado",
)


class HallazgoSeguimiento(SQLModel, table=True):
    """Entrada del historial de un hallazgo (ticket).

    Cada actualización (asignación, avance, solicitud/aprobación/rechazo de
    cierre) es una fila inmutable; el historial nunca se sobrescribe.
    """

    __tablename__ = "hallazgo_seguimiento"

    id: int | None = Field(default=None, primary_key=True)
    hallazgo_id: int = Field(foreign_key="hallazgo.id", index=True)
    usuario_id: int = Field(foreign_key="usuario.id")
    tipo: str = Field(max_length=30)
    detalle: str | None = Field(default=None, max_length=1000)
    estado_desde: str | None = Field(default=None, max_length=20)
    estado_hasta: str | None = Field(default=None, max_length=20)
    fecha_creacion: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    hallazgo: "Hallazgo" = Relationship(back_populates="seguimientos")
    usuario: "Usuario" = Relationship()
