from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel

from app.schemas.area import AreaRead
from app.schemas.celula import CelulaRead
from app.schemas.usuario import UsuarioRead


class EjecucionAuditoriaBase(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    fecha: datetime = Field(default_factory=datetime.utcnow)
    observaciones: str | None = Field(default=None, max_length=1000)
    estado: str = Field(default="en_proceso", max_length=20)


class EjecucionAuditoriaCreate(EjecucionAuditoriaBase):
    auditoria_id: int
    usuario_id: int
    celula_id: int | None = None


class EjecucionAuditoriaUpdate(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    fecha: datetime | None = None
    observaciones: str | None = Field(default=None, max_length=1000)
    estado: str | None = Field(default=None, max_length=20)
    auditoria_id: int | None = None
    usuario_id: int | None = None
    celula_id: int | None = None


class CriterioRespuesta(SQLModel):
    id: int
    descripcion: str
    orden: int
    respuesta_valor: str | None = None
    respuesta_observaciones: str | None = None
    respuesta_id: int | None = None
    hallazgo_id: int | None = None
    hallazgo_descripcion: str | None = None


class EjecucionAuditoriaRead(EjecucionAuditoriaBase):
    id: int
    auditoria_id: int
    usuario_id: int
    celula_id: int | None = None
    auditoria_nombre: str = ""
    area_nombre: str | None = None
    celula_numero: int | None = None
    auditor_nombre: str = ""
    criterios: list[CriterioRespuesta] = []


class EjecucionResumen(SQLModel):
    """Resumen de resultados V/A/R de una ejecucion."""

    total_criterios: int = 0
    total_v: int = 0
    total_a: int = 0
    total_r: int = 0


class EjecucionAuditoriaListItem(SQLModel):
    """Fila compacta del historial de ejecuciones."""

    id: int
    fecha: datetime
    estado: str
    auditoria_id: int
    auditoria_nombre: str = ""
    usuario_id: int
    usuario_nombre: str = ""
    celula_id: int | None = None
    celula_numero: int | None = None
    area_id: int | None = None
    area_nombre: str | None = None
    resumen: EjecucionResumen = EjecucionResumen()


class EjecucionAuditoriaDetalle(EjecucionAuditoriaRead):
    """Detalle completo de una ejecucion incluyendo resumen."""

    area_id: int | None = None
    resumen: EjecucionResumen = EjecucionResumen()


class IniciarEjecucionRequest(SQLModel):
    celula_id: int | None = None


class RespuestaItem(SQLModel):
    criterio_id: int
    valor: str = Field(max_length=20)
    observaciones: str | None = None


class GuardarRespuestasRequest(SQLModel):
    respuestas: list[RespuestaItem]


class OpcionesFiltrosRevision(SQLModel):
    """Opciones para los filtros de la revisión de auditorías."""

    areas: list[AreaRead] = []
    celulas: list[CelulaRead] = []
    auditores: list[UsuarioRead] = []
