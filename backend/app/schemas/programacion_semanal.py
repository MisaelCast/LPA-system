"""Esquemas de la planificación semanal de auditorías."""

from sqlmodel import SQLModel


class DiaPlanSemana(SQLModel):
    """Auditoría sorteada para un día hábil."""

    dia_semana: int
    fecha: str
    nombre_dia: str
    auditoria_id: int | None = None
    auditoria_nombre: str | None = None
    es_hoy: bool = False


class AreaPlanSemana(SQLModel):
    """Plan semanal (lunes a viernes) de un área."""

    area_id: int
    area_nombre: str
    dias: list[DiaPlanSemana]


class PlanSemanalRead(SQLModel):
    """Plan semanal visible para el usuario autenticado."""

    semana_inicio: str
    semana_fin: str
    areas: list[AreaPlanSemana]
