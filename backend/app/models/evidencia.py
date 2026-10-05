from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.hallazgo import Hallazgo


class Evidencia(SQLModel, table=True):
    """Archivo asociado a un hallazgo."""

    __tablename__ = "evidencia"

    id: int | None = Field(default=None, primary_key=True)
    ruta_archivo: str = Field(max_length=500)
    tipo_archivo: str = Field(default="fotografia", max_length=100)
    fecha_carga: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    hallazgo_id: int = Field(foreign_key="hallazgo.id")

    hallazgo: "Hallazgo" = Relationship(back_populates="evidencias")
