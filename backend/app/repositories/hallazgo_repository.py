"""Repositorio para la entidad Hallazgo."""

from sqlmodel import Session, select

from app.models.hallazgo import Hallazgo


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

    def listar_por_ejecucion(self, ejecucion_id: int) -> list[Hallazgo]:
        """Lista los hallazgos cuyas respuestas pertenecen a una ejecucion."""
        from app.models.respuesta import Respuesta

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