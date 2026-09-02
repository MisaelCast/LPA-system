from typing import TYPE_CHECKING, Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.criterio import Criterio
    from app.models.ejecucion_auditoria import EjecucionAuditoria
    from app.models.hallazgo import Hallazgo


class Respuesta(SQLModel, table=True):
    """Resultado observado para un criterio durante una ejecucion."""

    __tablename__ = "respuesta"
    __table_args__ = (
        UniqueConstraint(
            "ejecucion_auditoria_id",
            "criterio_id",
            name="uq_respuesta_ejecucion_criterio",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    valor: str = Field(max_length=20)
    observaciones: str | None = Field(default=None, max_length=1000)
    ejecucion_auditoria_id: int = Field(foreign_key="ejecucion_auditoria.id")
    criterio_id: int = Field(foreign_key="criterio.id")

    ejecucion_auditoria: "EjecucionAuditoria" = Relationship(back_populates="respuestas")
    criterio: "Criterio" = Relationship(back_populates="respuestas")
    hallazgo: Optional["Hallazgo"] = Relationship(
        back_populates="respuesta",
        sa_relationship_kwargs={"uselist": False},
    )
