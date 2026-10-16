"""Programación semanal de auditorías asignadas por sorteo (lunes a viernes)."""

from datetime import date

from sqlmodel import Field, SQLModel


class ProgramacionSemanal(SQLModel, table=True):
    """Asigna, por semana, una auditoría a cada día hábil (lunes a viernes).

    El calendario se genera una sola vez por semana y se conserva; las
    semanas anteriores no se modifican. ``dia_semana`` usa 0=Lunes..4=Viernes.
    """

    __tablename__ = "programacion_semanal"

    id: int | None = Field(default=None, primary_key=True)
    semana_inicio: date = Field(index=True)  # lunes de la semana
    dia_semana: int = Field(ge=0, le=4)
    auditoria_id: int = Field(foreign_key="auditoria.id")
