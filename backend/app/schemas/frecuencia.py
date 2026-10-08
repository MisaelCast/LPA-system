from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


class FrecuenciaBase(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    nombre: str = Field(max_length=100)
    descripcion: str | None = Field(default=None, max_length=255)
    dias: int = Field(ge=1)


class FrecuenciaCreate(FrecuenciaBase):
    pass


class FrecuenciaUpdate(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    nombre: str | None = Field(default=None, max_length=100)
    descripcion: str | None = Field(default=None, max_length=255)
    dias: int | None = Field(default=None, ge=1)


class FrecuenciaRead(FrecuenciaBase):
    id: int
