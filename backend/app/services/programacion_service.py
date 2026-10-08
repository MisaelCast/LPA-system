"""Generación automática de ejecuciones ``pendiente`` según la frecuencia."""

from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.models.area import Area
from app.models.auditoria import Auditoria
from app.models.celula import Celula
from app.models.ejecucion_auditoria import EjecucionAuditoria
from app.models.frecuencia import Frecuencia
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.models.usuario_area import UsuarioArea
from app.models.usuario_celula import UsuarioCelula


def _meses_desde_dias(dias: int) -> int:
    """Convierte días a meses para frecuencias mensuales o mayores."""
    if dias <= 15:
        return 1
    if dias <= 30:
        return 1
    if dias <= 60:
        return 2
    if dias <= 90:
        return 3
    return 12


def inicio_periodo(fecha: datetime, frecuencia: Frecuencia) -> datetime:
    """Devuelve el inicio (UTC) del periodo vigente para una frecuencia."""
    base = fecha.replace(hour=0, minute=0, second=0, microsecond=0)

    if frecuencia.dias == 1:  # Diaria: cada día calendario
        return base

    if frecuencia.dias == 7:  # Semanal: inicia lunes
        return base - timedelta(days=base.weekday())

    if frecuencia.dias == 15:  # Quincenal: días 1 y 16
        return base.replace(day=16) if fecha.day >= 16 else base.replace(day=1)

    # Mensual o mayor: día 1 del mes que inicia el periodo.
    meses = _meses_desde_dias(frecuencia.dias)
    mes_actual = fecha.month
    inicios = [1 + i * meses for i in range(12 // meses)]
    mes_inicio = max(m for m in inicios if m <= mes_actual)
    return fecha.replace(
        month=mes_inicio, day=1, hour=0, minute=0, second=0, microsecond=0
    )


def _existe_pendiente(
    session: Session,
    auditoria_id: int,
    celula_id: int | None,
    usuario_id: int,
    periodo: datetime,
) -> bool:
    fila = session.exec(
        select(EjecucionAuditoria).where(
            EjecucionAuditoria.auditoria_id == auditoria_id,
            EjecucionAuditoria.celula_id == celula_id,
            EjecucionAuditoria.usuario_id == usuario_id,
            EjecucionAuditoria.fecha_programada == periodo,
        )
    ).first()
    return fila is not None


def _crear_pendiente(
    session: Session,
    auditoria_id: int,
    celula_id: int | None,
    usuario_id: int,
    periodo: datetime,
) -> int:
    if _existe_pendiente(session, auditoria_id, celula_id, usuario_id, periodo):
        return 0
    session.add(
        EjecucionAuditoria(
            fecha=datetime.now(timezone.utc),
            fecha_programada=periodo,
            estado="pendiente",
            auditoria_id=auditoria_id,
            usuario_id=usuario_id,
            celula_id=celula_id,
        )
    )
    return 1


def _responsables_de_celula(
    session: Session, celula: Celula, area_id: int
) -> list[Usuario]:
    """Auditores responsables de una célula.

    Incluye a quienes tienen la célula asignada explícitamente y a quienes
    tienen el área asignada sin células específicas (cubren todas). Solo usa
    usuarios con rol **Auditor**.
    """
    responsables = list(
        session.exec(
            select(Usuario)
            .join(UsuarioCelula, Usuario.id == UsuarioCelula.usuario_id)
            .join(Rol, Usuario.rol_id == Rol.id)
            .where(
                UsuarioCelula.celula_id == celula.id,
                Rol.nombre == "Auditor",
                Usuario.activo == True,  # noqa: E712
            )
        ).all()
    )

    usuarios_con_celulas = set(
        session.exec(select(UsuarioCelula.usuario_id)).all()
    )
    area_ids_rows: list[int] = list(
        session.exec(
            select(UsuarioArea.usuario_id).where(UsuarioArea.area_id == area_id)
        ).all()
    )
    for usuario_id in area_ids_rows:
        if usuario_id in usuarios_con_celulas:
            continue
        usuario = session.get(Usuario, usuario_id)
        if usuario is None or not usuario.activo or usuario in responsables:
            continue
        rol = session.get(Rol, usuario.rol_id)
        if rol is not None and rol.nombre == "Auditor":
            responsables.append(usuario)

    return responsables


def _responsables_de_area(
    session: Session, area_id: int
) -> list[Usuario]:
    """Supervisores asignados a un área (para auditorías de verificación)."""
    return list(
        session.exec(
            select(Usuario)
            .join(UsuarioArea, Usuario.id == UsuarioArea.usuario_id)
            .join(Rol, Usuario.rol_id == Rol.id)
            .where(
                UsuarioArea.area_id == area_id,
                Rol.nombre == "Supervisor",
                Usuario.activo == True,  # noqa: E712
            )
        ).all()
    )


def generar_pendientes(
    session: Session, ahora: datetime | None = None
) -> dict:
    """Genera las ejecuciones ``pendiente`` del periodo vigente.

    Idempotente: no duplica una ejecución (auditoría × célula/área × usuario)
    para el mismo periodo.
    """
    ahora = ahora or datetime.now(timezone.utc)
    auditories = list(
        session.exec(select(Auditoria).where(Auditoria.activa == True)).all()
    )
    creadas = 0

    for auditoria in auditories:
        frecuencia = session.get(Frecuencia, auditoria.frecuencia_id)
        if frecuencia is None:
            continue
        periodo = inicio_periodo(ahora, frecuencia)

        if auditoria.tipo_respuesta == "cumplimiento":
            area = session.get(Area, auditoria.area_id)
            responsables = (
                _responsables_de_area(session, area.id) if area else []
            )
            for usuario in responsables:
                creadas += _crear_pendiente(
                    session, auditoria.id, None, usuario.id, periodo
                )
            continue

        # Auditorías de proceso: una pendiente por (auditoría × célula).
        if auditoria.area_id is None:
            continue
        celulas = list(
            session.exec(
                select(Celula).where(
                    Celula.area_id == auditoria.area_id,
                    Celula.activa == True,  # noqa: E712
                )
            ).all()
        )
        for celula in celulas:
            responsables = _responsables_de_celula(
                session, celula, auditoria.area_id
            )
            for usuario in responsables:
                creadas += _crear_pendiente(
                    session, auditoria.id, celula.id, usuario.id, periodo
                )

    session.commit()
    return {"creadas": creadas}