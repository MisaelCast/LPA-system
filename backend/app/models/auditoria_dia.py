"""Días hábiles elegidos para la recurrencia semanal de una auditoría."""

from sqlmodel import Field, SQLModel, UniqueConstraint


class AuditoriaDia(SQLModel, table=True):
    """Día hábil (0=Lunes..4=Viernes) en que una auditoría se ejecuta.

    Una auditoría con filas en esta tabla se ejecuta cada semana en los días
    elegidos (dentro del periodo de su frecuencia) y no participa en el
    sorteo semanal.
    """

    __tablename__ = "auditoria_dia"
    __table_args__ = (
        UniqueConstraint(
            "auditoria_id", "dia_semana", name="uq_auditoria_dia"
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    auditoria_id: int = Field(foreign_key="auditoria.id", index=True)
    dia_semana: int = Field(ge=0, le=4)


def dias_elegidos(auditoria) -> list[int]:
    """Días hábiles elegidos (0..4) de una auditoría; ``[]`` si no tiene.

    Lee primero el atributo enriquecido ``dias_semana`` (lista de enteros),
    luego la relación ``dias_rows`` sin forzar cargas sobre instancias
    desvinculadas (p. ej. objetos creados en pruebas).
    """
    valor = auditoria.__dict__.get("dias_semana")
    if isinstance(valor, list):
        return [d for d in valor if isinstance(d, int)]

    filas = auditoria.__dict__.get("dias_rows")
    if filas is None:
        try:
            filas = auditoria.dias_rows  # carga si está ligado a una sesión
        except Exception:
            return []
    return sorted({f.dia_semana for f in filas})
