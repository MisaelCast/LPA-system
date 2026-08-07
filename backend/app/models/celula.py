from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.area import Area
    from app.models.ejecucion_auditoria import EjecucionAuditoria


class Celula(SQLModel, table=True):
    """Linea o celula de produccion dentro de un area."""

    __tablename__ = "celula"
    __table_args__ = (UniqueConstraint("area_id", "numero"),)

    id: int | None = Field(default=None, primary_key=True)
    numero: int
    activa: bool = Field(default=True)
    area_id: int = Field(foreign_key="area.id")

    area: "Area" = Relationship(back_populates="celulas")
    ejecuciones_auditoria: list["EjecucionAuditoria"] = Relationship(
        back_populates="celula",
    )
