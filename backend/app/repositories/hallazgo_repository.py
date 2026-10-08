"""Repositorio para la entidad Hallazgo."""

from sqlmodel import Session, select

from app.models.auditoria import Auditoria
from app.models.ejecucion_auditoria import EjecucionAuditoria
from app.models.hallazgo import Hallazgo
from app.models.respuesta import Respuesta


class HallazgoRepository:
    """Acceso a datos para la tabla ``hallazgo``."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def obtener_por_id(self, hallazgo_id: int) -> Hallazgo | None:
        return self._session.exec(
            select(Hallazgo).where(Hallazgo.id == hallazgo_id)
        ).first()

    def obtener_por_respuesta(self, respuesta_id: int) -> Hallazgo | None:
        return self._session.exec(
            select(Hallazgo).where(Hallazgo.respuesta_id == respuesta_id)
        ).first()

    def listar(
        self,
        estado: str | None = None,
        area_responsable_id: int | None = None,
        solo_usuario_id: int | None = None,
        areas_ids: list[int] | None = None,
    ) -> list[Hallazgo]:
        """Lista hallazgos con filtros opcionales.

        ``solo_usuario_id`` limita a los hallazgos cuya ejecución pertenece a
        ese usuario (visibilidad del rol Auditor). ``areas_ids`` limita a los
        hallazgos de auditorías de esas áreas (visibilidad de Supervisor/Gerente).
        """
        stmt = select(Hallazgo)
        if estado:
            stmt = stmt.where(Hallazgo.estado == estado)
        if area_responsable_id:
            stmt = stmt.where(
                Hallazgo.area_responsable_id == area_responsable_id
            )
        if solo_usuario_id is not None or areas_ids:
            stmt = (
                stmt.join(Respuesta, Respuesta.id == Hallazgo.respuesta_id)
                .join(
                    EjecucionAuditoria,
                    EjecucionAuditoria.id == Respuesta.ejecucion_auditoria_id,
                )
            )
        if solo_usuario_id is not None:
            stmt = stmt.where(EjecucionAuditoria.usuario_id == solo_usuario_id)
        if areas_ids:
            stmt = (
                stmt.join(Auditoria, Auditoria.id == EjecucionAuditoria.auditoria_id)
                .where(Auditoria.area_id.in_(areas_ids))
            )
        stmt = stmt.order_by(Hallazgo.fecha_creacion.desc())
        return list(self._session.exec(stmt).all())

    def listar_por_ejecucion(self, ejecucion_id: int) -> list[Hallazgo]:
        """Lista los hallazgos cuyas respuestas pertenecen a una ejecucion."""
        return list(
            self._session.exec(
                select(Hallazgo)
                .join(Respuesta, Respuesta.id == Hallazgo.respuesta_id)
                .where(Respuesta.ejecucion_auditoria_id == ejecucion_id)
            ).all()
        )

    def crear(self, hallazgo: Hallazgo) -> Hallazgo:
        self._session.add(hallazgo)
        self._session.commit()
        self._session.refresh(hallazgo)
        return hallazgo

    def actualizar(self, hallazgo: Hallazgo) -> Hallazgo:
        self._session.merge(hallazgo)
        self._session.commit()
        self._session.refresh(hallazgo)
        return hallazgo

    def eliminar(self, hallazgo: Hallazgo) -> None:
        self._session.delete(hallazgo)
        self._session.commit()
