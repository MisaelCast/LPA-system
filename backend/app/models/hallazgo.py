from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.models.hallazgo_responsable import HallazgoResponsable

if TYPE_CHECKING:
    from app.models.area import Area
    from app.models.evidencia import Evidencia
    from app.models.respuesta import Respuesta
    from app.models.usuario import Usuario


ESTADOS_HALLAZGO = ("abierto", "en_proceso", "cerrado")


class Hallazgo(SQLModel, table=True):
    """Desviacion detectada durante una auditoria."""

    __tablename__ = "hallazgo"

    id: int | None = Field(default=None, primary_key=True)
    descripcion: str = Field(max_length=1000)
    fecha_creacion: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    respuesta_id: int = Field(foreign_key="respuesta.id", unique=True)

    estado: str = Field(default="abierto", max_length=20)
    accion_correctiva: str | None = Field(default=None, max_length=1000)
    area_responsable_id: int | None = Field(
        default=None, foreign_key="area.id"
    )
    fecha_cierre: datetime | None = Field(default=None)

    respuesta: "Respuesta" = Relationship(back_populates="hallazgo")
    evidencias: list["Evidencia"] = Relationship(back_populates="hallazgo")
    responsables: list["Usuario"] = Relationship(
        back_populates="hallazgos_responsables",
        link_model=HallazgoResponsable,
    )
    area_responsable: Optional["Area"] = Relationship()
