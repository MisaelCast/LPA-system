from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.models.hallazgo_responsable import HallazgoResponsable

if TYPE_CHECKING:
    from app.models.evidencia import Evidencia
    from app.models.respuesta import Respuesta
    from app.models.usuario import Usuario


class Hallazgo(SQLModel, table=True):
    """Desviacion detectada durante una auditoria."""

    __tablename__ = "hallazgo"

    id: int | None = Field(default=None, primary_key=True)
    descripcion: str = Field(max_length=1000)
    fecha_creacion: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    respuesta_id: int = Field(foreign_key="respuesta.id", unique=True)

    respuesta: "Respuesta" = Relationship(back_populates="hallazgo")
    evidencias: list["Evidencia"] = Relationship(back_populates="hallazgo")
    responsables: list["Usuario"] = Relationship(
        back_populates="hallazgos_responsables",
        link_model=HallazgoResponsable,
    )
