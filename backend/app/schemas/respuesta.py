from pydantic import ConfigDict, field_validator
from sqlmodel import Field, SQLModel

_VALORES_PERMITIDOS: set[str] = {"V", "A", "R"}


def _validar_valor(v: str | None) -> str | None:
    if v is not None and v not in _VALORES_PERMITIDOS:
        raise ValueError(
            f"Valor de respuesta inválido '{v}'. "
            f"Debe ser uno de: {', '.join(sorted(_VALORES_PERMITIDOS))}"
        )
    return v


class RespuestaBase(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    valor: str = Field(max_length=20)
    observaciones: str | None = Field(default=None, max_length=1000)

    @field_validator("valor")
    @classmethod
    def validar_valor(cls, v: str) -> str:
        return _validar_valor(v)  # type: ignore[return-value]


class RespuestaCreate(RespuestaBase):
    ejecucion_auditoria_id: int
    criterio_id: int


class RespuestaUpdate(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    valor: str | None = Field(default=None, max_length=20)
    observaciones: str | None = Field(default=None, max_length=1000)
    ejecucion_auditoria_id: int | None = None
    criterio_id: int | None = None

    @field_validator("valor")
    @classmethod
    def validar_valor(cls, v: str | None) -> str | None:
        return _validar_valor(v)


class RespuestaRead(RespuestaBase):
    id: int
    ejecucion_auditoria_id: int
    criterio_id: int
