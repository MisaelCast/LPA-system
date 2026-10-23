from pydantic import ConfigDict, computed_field, field_validator
from sqlmodel import Field, SQLModel


def _normalizar_dias(v):
    """Normaliza los días hábiles elegidos: enteros 0..4 únicos y ordenados."""
    if v is None:
        return None
    if not isinstance(v, list):
        raise ValueError(
            "dias_semana debe ser una lista de días (0=Lunes..4=Viernes)."
        )
    dias: set[int] = set()
    for item in v:
        try:
            dia = int(item)
        except (TypeError, ValueError):
            raise ValueError(
                "dias_semana debe contener números de día (0=Lunes..4=Viernes)."
            ) from None
        if dia < 0 or dia > 4:
            raise ValueError(
                "Los días elegidos van de 0 (lunes) a 4 (viernes)."
            )
        dias.add(dia)
    return sorted(dias)


class AuditoriaBase(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    nombre: str = Field(max_length=150)
    descripcion: str | None = Field(default=None, max_length=500)
    activa: bool = Field(default=True)
    tipo_respuesta: str = Field(default="semaforo", max_length=20)
    dia_semana: int | None = Field(default=None, ge=0, le=6)
    # Días hábiles en que la auditoría se ejecuta cada semana (recurrencia
    # elegida por quien la crea). Vacío = se comporta según la frecuencia.
    dias_semana: list[int] = Field(default_factory=list)

    @field_validator("dias_semana", mode="before")
    @classmethod
    def _validar_dias_semana(cls, v):
        return _normalizar_dias(v)


class AuditoriaCreate(AuditoriaBase):
    capa_id: int
    frecuencia_id: int
    area_id: int | None = None


class AuditoriaUpdate(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    nombre: str | None = Field(default=None, max_length=150)
    descripcion: str | None = Field(default=None, max_length=500)
    activa: bool | None = None
    tipo_respuesta: str | None = Field(default=None, max_length=20)
    dia_semana: int | None = Field(default=None, ge=0, le=6)
    # ``None`` = no modificar; lista (aunque sea vacía) = reemplazar los días.
    dias_semana: list[int] | None = None
    capa_id: int | None = None
    frecuencia_id: int | None = None
    area_id: int | None = None

    @field_validator("dias_semana", mode="before")
    @classmethod
    def _validar_dias_semana(cls, v):
        return _normalizar_dias(v)


class AuditoriaRead(AuditoriaBase):
    id: int
    capa_id: int
    frecuencia_id: int
    area_id: int | None = None
    capa_nombre: str = ""
    frecuencia_nombre: str = ""
    area_nombre: str | None = None
    requiere_celula: bool = True


class AuditoriaEstadoUpdate(SQLModel):
    activa: bool
