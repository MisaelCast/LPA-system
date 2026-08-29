"""Repositorio para la entidad EjecucionAuditoria."""

from datetime import datetime

from sqlmodel import Session, select

from app.models.ejecucion_auditoria import EjecucionAuditoria


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
    ) -> list[EjecucionAuditoria]:
        """Lista ejecuciones con filtros opcionales, ordenadas por fecha DESC."""
        statement = select(EjecucionAuditoria)

        if auditoria_id is not None:
            statement = statement.where(
                EjecucionAuditoria.auditoria_id == auditoria_id
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
