from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


class CapaBase(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    nombre: str = Field(max_length=100)
    descripcion: str | None = Field(default=None, max_length=255)
    activa: bool = Field(default=True)


class CapaCreate(CapaBase):
    pass


class CapaUpdate(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    nombre: str | None = Field(default=None, max_length=100)
    descripcion: str | None = Field(default=None, max_length=255)
    activa: bool | None = None


class CapaRead(CapaBase):
    id: int


class CapaEstadoUpdate(SQLModel):
    activa: bool
