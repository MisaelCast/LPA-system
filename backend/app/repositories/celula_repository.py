"""Repositorio para la entidad Celula."""

from sqlmodel import Session, select

from app.models.celula import Celula


class CelulaRepository:
    """Acceso a datos para la tabla ``celula``."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def obtener_por_id(self, celula_id: int) -> Celula | None:
        """Busca una celula por su identificador unico."""
        return self._session.exec(
            select(Celula).where(Celula.id == celula_id)
        ).first()

    def obtener_por_area_y_numero(
        self, area_id: int, numero: int
    ) -> Celula | None:
        """Busca una celula por area y numero."""
        return self._session.exec(
            select(Celula).where(
                Celula.area_id == area_id,
                Celula.numero == numero,
            )
        ).first()

    def listar_por_area(
        self, area_id: int, skip: int = 0, limit: int = 100
    ) -> list[Celula]:
        """Lista celulas de un area con paginacion basica."""
        return list(
            self._session.exec(
                select(Celula)
                .where(Celula.area_id == area_id)
                .offset(skip)
                .limit(limit)
            ).all()
        )

    def crear(self, celula: Celula) -> Celula:
        """Inserta una nueva celula en la base de datos."""
        self._session.add(celula)
        self._session.commit()
        self._session.refresh(celula)
        return celula

    def actualizar(self, celula: Celula) -> Celula:
        """Actualiza los datos de una celula existente."""
        self._session.merge(celula)
        self._session.commit()
        self._session.refresh(celula)
        return celula
