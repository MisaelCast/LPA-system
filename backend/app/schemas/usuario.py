from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


class UsuarioBase(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    nombre: str = Field(max_length=150)
    correo: str = Field(max_length=255)
    activo: bool = Field(default=True)


class UsuarioCreate(UsuarioBase):
    contrasena: str = Field(max_length=255)
    rol_id: int


class UsuarioUpdate(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    nombre: str | None = Field(default=None, max_length=150)
    correo: str | None = Field(default=None, max_length=255)
    contrasena: str | None = Field(default=None, max_length=255)
    activo: bool | None = None
    rol_id: int | None = None


class UsuarioRead(UsuarioBase):
    id: int


class UsuarioLogin(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    correo: str = Field(max_length=255)
    contrasena: str = Field(max_length=255)


class Token(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    access_token: str
    token_type: str


class DatosToken(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    usuario_id: int | None = None


class UsuarioEstadoUpdate(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    activo: bool
