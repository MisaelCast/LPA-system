from datetime import datetime
from typing import Optional

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


class HallazgoBase(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    descripcion: str = Field(max_length=1000)


class HallazgoCreate(HallazgoBase):
    respuesta_id: int


class HallazgoUpdate(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    descripcion: str | None = Field(default=None, max_length=1000)


class HallazgoRead(HallazgoBase):
    id: int
    fecha_creacion: datetime
    respuesta_id: int


class HallazgoDetallado(HallazgoRead):
    """Hallazgo enriquecido con el contexto de ejecucion, auditoria, celula y criterio.

    El tipo (``A`` o ``R``) se obtiene desde la respuesta relacionada.
    """

    tipo: str
    respuesta_valor: str
    criterio_id: int
    criterio_descripcion: str
    criterio_orden: int
    ejecucion_id: int
    ejecucion_estado: str
    auditoria_id: int
    auditoria_nombre: str
    celula_id: Optional[int] = None
    celula_numero: Optional[int] = None