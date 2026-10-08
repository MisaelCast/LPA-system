from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.auditoria import Auditoria


class Frecuencia(SQLModel, table=True):
    """Periodicidad con la que debe ejecutarse una auditoria."""

    __tablename__ = "frecuencia"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100, unique=True, index=True)
    descripcion: str | None = Field(default=None, max_length=255)
    dias: int = Field(ge=1)

    auditorias: list["Auditoria"] = Relationship(back_populates="frecuencia")
