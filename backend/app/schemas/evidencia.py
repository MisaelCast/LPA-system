from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


class EvidenciaBase(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    ruta_archivo: str = Field(max_length=500)
    tipo_archivo: str = Field(default="fotografia", max_length=100)


class EvidenciaCreate(EvidenciaBase):
    hallazgo_id: int


class EvidenciaUpdate(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    ruta_archivo: str | None = Field(default=None, max_length=500)
    tipo_archivo: str | None = Field(default=None, max_length=100)
    hallazgo_id: int | None = None


class EvidenciaRead(EvidenciaBase):
    id: int
    fecha_carga: datetime
    hallazgo_id: int


class EvidenciaOut(SQLModel):
    """Evidencia para el frontend, con URL firmada (transitoria)."""

    id: int
    fecha_carga: datetime
    tipo_archivo: str
    url: str | None = None
