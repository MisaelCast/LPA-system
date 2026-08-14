"""Repositorio para la entidad EjecucionAuditoria."""

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
