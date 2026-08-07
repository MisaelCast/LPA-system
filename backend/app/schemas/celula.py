from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


class CelulaBase(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    numero: int = Field(ge=1)
    activa: bool = Field(default=True)


class CelulaCreate(CelulaBase):
    pass


class CelulaUpdate(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    numero: int | None = Field(default=None, ge=1)
    activa: bool | None = None


class CelulaRead(CelulaBase):
    id: int
    area_id: int


class CelulaEstadoUpdate(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    activa: bool
