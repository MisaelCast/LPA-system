from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.auditoria import Auditoria


class Capa(SQLModel, table=True):
    """Nivel jerarquico dentro del proceso LPA."""

    __tablename__ = "capa"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100, unique=True, index=True)
    descripcion: str | None = Field(default=None, max_length=255)
    activa: bool = Field(default=True)

    auditorias: list["Auditoria"] = Relationship(back_populates="capa")
