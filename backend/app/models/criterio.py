from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.auditoria import Auditoria
    from app.models.respuesta import Respuesta


class Criterio(SQLModel, table=True):
    """Punto de inspeccion dentro de una auditoria."""

    __tablename__ = "criterio"

    id: int | None = Field(default=None, primary_key=True)
    descripcion: str = Field(max_length=500)
    orden: int = Field(default=1, ge=1)
    activo: bool = Field(default=True)
    auditoria_id: int = Field(foreign_key="auditoria.id")

    # Jerarquía opcional para agrupar criterios bajo títulos/subtítulos
    # sin repetirlos dentro de ``descripcion``. La interfaz los presenta
    # como encabezados/separadores visuales.
    seccion: str | None = Field(default=None, max_length=150)
    subseccion: str | None = Field(default=None, max_length=150)
    subtitulo: str | None = Field(default=None, max_length=150)

    auditoria: "Auditoria" = Relationship(back_populates="criterios")
    respuestas: list["Respuesta"] = Relationship(back_populates="criterio")
