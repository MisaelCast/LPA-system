from datetime import datetime
from typing import Optional

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


class HallazgoBase(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    descripcion: str = Field(max_length=1000)


class HallazgoCreateRequest(HallazgoBase):
    """Body del POST: el ``respuesta_id`` viene en el path.

    ``area_responsable_id`` es opcional: para auditorías de verificación se
    hereda automáticamente el área de la auditoría.
    """

    area_responsable_id: int | None = None


class HallazgoCreate(HallazgoBase):
    respuesta_id: int
    area_responsable_id: int | None = None


class HallazgoUpdate(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    descripcion: str | None = Field(default=None, max_length=1000)


class HallazgoSeguimientoUpdate(SQLModel):
    """Actualiza el seguimiento del hallazgo (estado, acción y área)."""

    model_config = ConfigDict(from_attributes=True)

    estado: str | None = Field(default=None, max_length=20)
    accion_correctiva: str | None = Field(default=None, max_length=1000)
    area_responsable_id: int | None = None


class HallazgoRead(HallazgoBase):
    id: int
    fecha_creacion: datetime
    respuesta_id: int
    estado: str = "abierto"
    accion_correctiva: str | None = None
    area_responsable_id: int | None = None
    area_responsable_nombre: str | None = None
    fecha_cierre: datetime | None = None


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
    auditor_id: int = 0
    celula_id: Optional[int] = None
    celula_numero: Optional[int] = None
