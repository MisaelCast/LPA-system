from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


class AreaBase(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    nombre: str = Field(max_length=150)
    descripcion: str | None = Field(default=None, max_length=255)
    activa: bool = Field(default=True)


class AreaCreate(AreaBase):
    pass


class AreaUpdate(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    nombre: str | None = Field(default=None, max_length=150)
    descripcion: str | None = Field(default=None, max_length=255)
    activa: bool | None = None


class AreaRead(AreaBase):
    id: int


class AreaEstadoUpdate(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    activa: bool
