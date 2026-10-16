"""Sorteo y conservación del calendario semanal de auditorías.

Cada semana se barajan las auditorías con ``programacion_semanal`` y se asigna
una a cada día hábil (lunes a viernes). El calendario se genera una sola vez
por semana; las semanas anteriores nunca se modifican.
"""

import random
from datetime import date, datetime, timedelta

from sqlmodel import Session, select

from app.models.auditoria import Auditoria
from app.models.programacion_semanal import ProgramacionSemanal

DIAS_HABILES = 5  # 0=Lunes .. 4=Viernes


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
