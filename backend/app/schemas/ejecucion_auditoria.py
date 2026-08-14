from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


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


class IniciarEjecucionRequest(SQLModel):
    celula_id: int | None = None


class RespuestaItem(SQLModel):
    criterio_id: int
    valor: str = Field(max_length=20)
    observaciones: str | None = None


class GuardarRespuestasRequest(SQLModel):
    respuestas: list[RespuestaItem]
