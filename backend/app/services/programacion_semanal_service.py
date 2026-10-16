"""Sorteo y conservación del calendario semanal de auditorías.

Cada semana se barajan las auditorías con ``programacion_semanal`` y se asigna
una a cada día hábil (lunes a viernes). El calendario se genera una sola vez
por semana; las semanas anteriores nunca se modifican.
"""

import random
from datetime import date, datetime, timedelta

from sqlmodel import Session, select

from app.models.area import Area
from app.models.auditoria import Auditoria
from app.models.programacion_semanal import ProgramacionSemanal
from app.schemas.programacion_semanal import (
    AreaPlanSemana,
    DiaPlanSemana,
    PlanSemanalRead,
)
from app.utils.tiempo import ahora_business

DIAS_HABILES = 5  # 0=Lunes .. 4=Viernes
DIAS_NOMBRE = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes")

# Estos roles solo ven las áreas que tienen asignadas.
_ROLES_CON_AREAS_ASIGNADAS = ("Auditor", "Supervisor", "Gerente")


def lunes_de(fecha: datetime | date) -> date:
    """Devuelve el lunes de la semana a la que pertenece ``fecha``."""
    dia = fecha.date() if isinstance(fecha, datetime) else fecha
    return dia - timedelta(days=dia.weekday())


def asegurar_semana(
    session: Session,
    auditorias: list[Auditoria],
    semana_inicio: date,
) -> list[ProgramacionSemanal]:
    """Garantiza el calendario de la semana; lo crea solo si aún no existe.

    Es idempotente: si la semana ya tiene asignaciones (para este conjunto de
    auditorías) no vuelve a barajar ni modifica las asignaciones previas.
    """
    ids = [a.id for a in auditorias if a.id is not None]
    if not ids:
        return []

    existentes = list(
        session.exec(
            select(ProgramacionSemanal).where(
                ProgramacionSemanal.semana_inicio == semana_inicio,
                ProgramacionSemanal.auditoria_id.in_(ids),
            )
        ).all()
    )
    if existentes:
        return existentes

    barajadas = list(auditorias)
    random.shuffle(barajadas)

    creadas: list[ProgramacionSemanal] = []
    dias_usados: set[int] = set()
    # Reparte las auditorías entre los días hábiles 0..4 (una por día).
    for indice, auditoria in enumerate(barajadas):
        # Cicla los días si hay más auditorías que días (no ocurre con 5).
        dia = indice % DIAS_HABILES
        if dia in dias_usados:
            continue
        dias_usados.add(dia)
        fila = ProgramacionSemanal(
            semana_inicio=semana_inicio,
            dia_semana=dia,
            auditoria_id=auditoria.id,
        )
        session.add(fila)
        creadas.append(fila)

    session.commit()
    return creadas


def calendario_de_semana(
    session: Session,
    auditorias: list[Auditoria],
    ahora: datetime,
) -> dict[int, Auditoria]:
    """Mapea ``dia_semana`` (0..4) -> auditoría para la semana de ``ahora``."""
    if not auditorias:
        return {}
    filas = asegurar_semana(session, auditorias, lunes_de(ahora))
    por_id = {a.id: a for a in auditorias}
    return {
        fila.dia_semana: por_id[fila.auditoria_id]
        for fila in filas
        if fila.auditoria_id in por_id
    }


def auditoria_del_dia(
    session: Session,
    auditorias: list[Auditoria],
    ahora: datetime,
) -> Auditoria | None:
    """Auditoría programada para el día de ``ahora`` (None en fin de semana)."""
    if ahora.weekday() >= DIAS_HABILES:
        return None
    return calendario_de_semana(session, auditorias, ahora).get(ahora.weekday())


def _areas_visibles(usuario) -> set[int] | None:
    """Áreas que el usuario puede ver; ``None`` significa todas."""
    rol = getattr(getattr(usuario, "rol", None), "nombre", "")
    if rol in _ROLES_CON_AREAS_ASIGNADAS:
        return {a.id for a in usuario.areas if a.id is not None}
    return None


def plan_semanal_usuario(
    session: Session,
    usuario,
    ahora: datetime | None = None,
) -> PlanSemanalRead:
    """Plan lunes a viernes de las auditorías con sorteo semanal.

    Las auditorías se muestran agrupadas por área, limitadas a las áreas
    asignadas del usuario (salvo Administrador, que ve todas).
    """
    ahora = ahora or ahora_business()
    lunes = lunes_de(ahora)
    visibles = _areas_visibles(usuario)

    auditorias = [
        a
        for a in session.exec(
            select(Auditoria).where(
                Auditoria.activa == True,  # noqa: E712
                Auditoria.programacion_semanal == True,  # noqa: E712
            )
        ).all()
        if visibles is None or (a.area_id is not None and a.area_id in visibles)
    ]

    por_area: dict[int, list[Auditoria]] = {}
    for auditoria in auditorias:
        if auditoria.area_id is not None:
            por_area.setdefault(auditoria.area_id, []).append(auditoria)

    areas: list[AreaPlanSemana] = []
    for area_id, grupo in por_area.items():
        area = session.get(Area, area_id)
        calendario = calendario_de_semana(session, grupo, ahora)
        dias = [
            DiaPlanSemana(
                dia_semana=dia,
                fecha=(lunes + timedelta(days=dia)).isoformat(),
                nombre_dia=DIAS_NOMBRE[dia],
                auditoria_id=(auditoria.id if auditoria else None),
                auditoria_nombre=(auditoria.nombre if auditoria else None),
                es_hoy=(lunes + timedelta(days=dia) == ahora.date()),
            )
            for dia in range(DIAS_HABILES)
            for auditoria in [calendario.get(dia)]
        ]
        areas.append(
            AreaPlanSemana(
                area_id=area_id,
                area_nombre=area.nombre if area else f"Área {area_id}",
                dias=dias,
            )
        )

    return PlanSemanalRead(
        semana_inicio=lunes.isoformat(),
        semana_fin=(lunes + timedelta(days=DIAS_HABILES + 1)).isoformat(),
        areas=sorted(areas, key=lambda a: a.area_nombre),
    )

