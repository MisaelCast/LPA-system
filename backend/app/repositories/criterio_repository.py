"""Repositorio para la entidad Criterio."""

from sqlmodel import Session, func, select
from sqlmodel.sql.expression import SelectOfScalar

from app.models.criterio import Criterio


class CriterioRepository:
    """Acceso a datos para la tabla ``criterio``."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def obtener_por_id(self, criterio_id: int) -> Criterio | None:
        """Busca un criterio por su identificador unico."""
        return self._session.exec(
            select(Criterio).where(Criterio.id == criterio_id)
        ).first()

    def listar_por_auditoria(self, auditoria_id: int) -> list[Criterio]:
        """Lista criterios de una auditoria ordenados por orden."""
        return list(
            self._session.exec(
                select(Criterio)
                .where(Criterio.auditoria_id == auditoria_id)
                .order_by(Criterio.orden)
            ).all()
        )

    def max_orden(self, auditoria_id: int) -> int:
        """Retorna el maximo orden actual para una auditoria."""
        result = self._session.exec(
            select(func.max(Criterio.orden)).where(
                Criterio.auditoria_id == auditoria_id
            )
        ).first()
        return result or 0

    def obtener_por_auditoria_y_orden(
        self, auditoria_id: int, orden: int
    ) -> Criterio | None:
        """Busca un criterio por auditoria y orden."""
        return self._session.exec(
            select(Criterio).where(
                Criterio.auditoria_id == auditoria_id,
                Criterio.orden == orden,
            )
        ).first()

    def crear(self, criterio: Criterio) -> Criterio:
        """Inserta un nuevo criterio en la base de datos."""
        self._session.add(criterio)
        self._session.commit()
        self._session.refresh(criterio)
        return criterio

    def actualizar(self, criterio: Criterio) -> Criterio:
        """Actualiza los datos de un criterio existente."""
        self._session.merge(criterio)
        self._session.commit()
        self._session.refresh(criterio)
        return criterio
