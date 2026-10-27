from datetime import datetime
from typing import Optional

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel

from app.schemas.evidencia import EvidenciaOut


class HallazgoBase(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    descripcion: str = Field(max_length=1000)


class HallazgoCreateRequest(HallazgoBase):
    """Body del POST: el ``respuesta_id`` viene en el path.

    ``area_responsable_id`` es opcional: para auditorías de verificación se
    hereda automáticamente el área de la auditoría.

    ``responsable_id`` asigna al Responsable de Manufactura de esa área; si
    no se envía, el hallazgo queda sin responsable hasta que se asigne.
    """

    area_responsable_id: int | None = None
    responsable_id: int | None = None
    fecha_limite: datetime | None = None


class HallazgoCreate(HallazgoBase):
    respuesta_id: int
    area_responsable_id: int | None = None
    responsable_id: int | None = None
    fecha_limite: datetime | None = None


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
    fecha_limite: datetime | None = None


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
    evidencias: list[EvidenciaOut] = Field(default_factory=list)
    responsable_id: int | None = None
    responsable_nombre: str | None = None
    atrasado: bool = False
    dias_sin_actualizar: int | None = None
    reincidente: bool = False


class ResponsableAsignarRequest(SQLModel):
    """Asigna (o reasigna) el responsable de un hallazgo."""

    model_config = ConfigDict(from_attributes=True)

    responsable_id: int
    fecha_limite: datetime | None = None


class AvanceTicketRequest(SQLModel):
    """Avance registrado por el responsable (acción correctiva y/o comentario)."""

    model_config = ConfigDict(from_attributes=True)

    accion_correctiva: str | None = Field(default=None, max_length=1000)
    comentario: str | None = Field(default=None, max_length=1000)


class CierreSolicitudRequest(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    comentario: str | None = Field(default=None, max_length=1000)


class CierreResolucionRequest(SQLModel):
    """El auditor aprueba o rechaza la solicitud de cierre."""

    model_config = ConfigDict(from_attributes=True)

    aprobar: bool
    observacion: str | None = Field(default=None, max_length=1000)


class SeguimientoRead(SQLModel):
    """Entrada del historial (trazabilidad) de un hallazgo."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    hallazgo_id: int
    usuario_id: int
    usuario_nombre: str
    tipo: str
    detalle: str | None = None
    estado_desde: str | None = None
    estado_hasta: str | None = None
    fecha_creacion: datetime


class ResponsableResumen(SQLModel):
    """Responsable de Manufactura disponible para asignar a un hallazgo."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    correo: str
