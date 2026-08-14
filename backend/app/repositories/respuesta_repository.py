"""Repositorio para la entidad Respuesta."""

from sqlmodel import Session, select

from app.models.respuesta import Respuesta


class RespuestaRepository:
    """Acceso a datos para la tabla ``respuesta``."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def obtener_por_id(self, respuesta_id: int) -> Respuesta | None:
        return self._session.exec(
            select(Respuesta).where(Respuesta.id == respuesta_id)
        ).first()

    def obtener_por_ejecucion_y_criterio(
        self, ejecucion_id: int, criterio_id: int
    ) -> Respuesta | None:
        return self._session.exec(
            select(Respuesta).where(
                Respuesta.ejecucion_auditoria_id == ejecucion_id,
                Respuesta.criterio_id == criterio_id,
            )
        ).first()

    def listar_por_ejecucion(self, ejecucion_id: int) -> list[Respuesta]:
        return list(
            self._session.exec(
                select(Respuesta).where(
                    Respuesta.ejecucion_auditoria_id == ejecucion_id
                )
            ).all()
        )

    def crear(self, respuesta: Respuesta) -> Respuesta:
        self._session.add(respuesta)
        self._session.commit()
        self._session.refresh(respuesta)
        return respuesta

    def actualizar(self, respuesta: Respuesta) -> Respuesta:
        self._session.merge(respuesta)
        self._session.commit()
        self._session.refresh(respuesta)
        return respuesta
