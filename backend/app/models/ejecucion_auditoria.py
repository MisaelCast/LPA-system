from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.auditoria import Auditoria
    from app.models.celula import Celula
    from app.models.respuesta import Respuesta
    from app.models.usuario import Usuario


class EjecucionAuditoria(SQLModel, table=True):
    """Auditoria realizada por un usuario en una fecha determinada."""

    __tablename__ = "ejecucion_auditoria"

    id: int | None = Field(default=None, primary_key=True)
    fecha: datetime = Field(default_factory=datetime.utcnow)
    observaciones: str | None = Field(default=None, max_length=1000)
    estado: str = Field(default="en_proceso", max_length=20)
    auditoria_id: int = Field(foreign_key="auditoria.id")
    usuario_id: int = Field(foreign_key="usuario.id")
    celula_id: int | None = Field(default=None, foreign_key="celula.id")

    auditoria: "Auditoria" = Relationship(back_populates="ejecuciones_auditoria")
    usuario: "Usuario" = Relationship(back_populates="ejecuciones_auditoria")
    celula: Optional["Celula"] = Relationship(back_populates="ejecuciones_auditoria")
    respuestas: list["Respuesta"] = Relationship(back_populates="ejecucion_auditoria")
