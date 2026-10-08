"""Repositorio para la entidad EjecucionAuditoria."""

from datetime import datetime

from sqlmodel import Session, select

from app.models.auditoria import Auditoria
from app.models.ejecucion_auditoria import EjecucionAuditoria
from app.models.rol import Rol
from app.models.usuario import Usuario


class EjecucionAuditoriaRepository:
    """Acceso a datos para la tabla ``ejecucion_auditoria``."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def obtener_por_id(self, ejecucion_id: int) -> EjecucionAuditoria | None:
        return self._session.exec(
            select(EjecucionAuditoria).where(EjecucionAuditoria.id == ejecucion_id)
        ).first()

    def listar(self, skip: int = 0, limit: int = 100) -> list[EjecucionAuditoria]:
        return list(
            self._session.exec(
                select(EjecucionAuditoria).offset(skip).limit(limit)
            ).all()
        )

    def listar_con_filtros(
        self,
        skip: int = 0,
        limit: int = 100,
        auditoria_id: int | None = None,
        celula_id: int | None = None,
        usuario_id: int | None = None,
        estado: str | None = None,
        fecha_desde: datetime | None = None,
        fecha_hasta: datetime | None = None,
        area_id: int | None = None,
        areas_ids: list[int] | None = None,
        tipo_respuesta: str | None = None,
        solo_auditores: bool = False,
    ) -> list[EjecucionAuditoria]:
        """Lista ejecuciones con filtros opcionales, ordenadas por fecha DESC.

        Las ejecuciones de usuarios desactivados se ocultan de los listados
        (permanecen almacenadas en BD), de modo que no aparecen a las capas
        superiores de revisión/verificación.
        """
        statement = (
            select(EjecucionAuditoria)
            .join(Usuario, EjecucionAuditoria.usuario_id == Usuario.id)
            .where(Usuario.activo == True)  # noqa: E712
        )

        if auditoria_id is not None:
            statement = statement.where(
                EjecucionAuditoria.auditoria_id == auditoria_id
            )
        if area_id is not None or areas_ids or tipo_respuesta is not None:
            statement = statement.join(
                Auditoria,
                EjecucionAuditoria.auditoria_id == Auditoria.id,
            )
        if area_id is not None:
            statement = statement.where(Auditoria.area_id == area_id)
        if areas_ids:
            statement = statement.where(Auditoria.area_id.in_(areas_ids))
        if tipo_respuesta is not None:
            statement = statement.where(Auditoria.tipo_respuesta == tipo_respuesta)
        if solo_auditores:
            statement = (
                statement.join(Rol, Usuario.rol_id == Rol.id)
                .where(Rol.nombre == "Auditor")
            )
        if celula_id is not None:
            statement = statement.where(EjecucionAuditoria.celula_id == celula_id)
        if usuario_id is not None:
            statement = statement.where(EjecucionAuditoria.usuario_id == usuario_id)
        if estado is not None:
            statement = statement.where(EjecucionAuditoria.estado == estado)
        if fecha_desde is not None:
            statement = statement.where(EjecucionAuditoria.fecha >= fecha_desde)
        if fecha_hasta is not None:
            statement = statement.where(EjecucionAuditoria.fecha <= fecha_hasta)

        statement = statement.order_by(EjecucionAuditoria.fecha.desc())
        statement = statement.offset(skip).limit(limit)

        return list(self._session.exec(statement).all())

    def listar_por_auditoria(self, auditoria_id: int) -> list[EjecucionAuditoria]:
        return list(
            self._session.exec(
                select(EjecucionAuditoria).where(
                    EjecucionAuditoria.auditoria_id == auditoria_id
                )
            ).all()
        )

    def crear(self, ejecucion: EjecucionAuditoria) -> EjecucionAuditoria:
        self._session.add(ejecucion)
        self._session.commit()
        self._session.refresh(ejecucion)
        return ejecucion

    def actualizar(self, ejecucion: EjecucionAuditoria) -> EjecucionAuditoria:
        self._session.merge(ejecucion)
        self._session.commit()
        self._session.refresh(ejecucion)
        return ejecucion
