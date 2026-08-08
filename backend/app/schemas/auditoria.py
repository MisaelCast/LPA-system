from pydantic import ConfigDict, computed_field
from sqlmodel import Field, SQLModel


class AuditoriaBase(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    nombre: str = Field(max_length=150)
    descripcion: str | None = Field(default=None, max_length=500)
    activa: bool = Field(default=True)


class AuditoriaCreate(AuditoriaBase):
    capa_id: int
    frecuencia_id: int
    area_id: int | None = None


class AuditoriaUpdate(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    nombre: str | None = Field(default=None, max_length=150)
    descripcion: str | None = Field(default=None, max_length=500)
    activa: bool | None = None
    capa_id: int | None = None
    frecuencia_id: int | None = None
    area_id: int | None = None


class AuditoriaRead(AuditoriaBase):
    id: int
    capa_id: int
    frecuencia_id: int
    area_id: int | None = None
    capa_nombre: str = ""
    frecuencia_nombre: str = ""
    area_nombre: str | None = None


class AuditoriaEstadoUpdate(SQLModel):
    activa: bool
