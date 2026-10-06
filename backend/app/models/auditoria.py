from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.area import Area
    from app.models.capa import Capa
    from app.models.criterio import Criterio
    from app.models.ejecucion_auditoria import EjecucionAuditoria
    from app.models.frecuencia import Frecuencia


class Auditoria(SQLModel, table=True):
    """Auditoria disponible dentro del sistema."""

    __tablename__ = "auditoria"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=150, index=True)
    descripcion: str | None = Field(default=None, max_length=500)
    activa: bool = Field(default=True)
    tipo_respuesta: str = Field(default="semaforo", max_length=20)
    capa_id: int = Field(foreign_key="capa.id")
    frecuencia_id: int = Field(foreign_key="frecuencia.id")
    area_id: int | None = Field(default=None, foreign_key="area.id")

    capa: "Capa" = Relationship(back_populates="auditorias")
    frecuencia: "Frecuencia" = Relationship(back_populates="auditorias")
    area: Optional["Area"] = Relationship(back_populates="auditorias")
    criterios: list["Criterio"] = Relationship(back_populates="auditoria")
    ejecuciones_auditoria: list["EjecucionAuditoria"] = Relationship(
        back_populates="auditoria",
    )
