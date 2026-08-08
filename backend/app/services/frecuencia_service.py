"""Logica de negocio para la entidad Frecuencia."""

from sqlmodel import Session

from app.models.frecuencia import Frecuencia
from app.repositories.frecuencia_repository import FrecuenciaRepository


class FrecuenciaService:
    """Servicio que encapsula la logica de negocio de frecuencias."""

    def __init__(self, session: Session) -> None:
        self._repo = FrecuenciaRepository(session)

    def listar(self) -> list[Frecuencia]:
        """Obtiene el listado completo de frecuencias."""
        return self._repo.listar()

    def obtener_por_id(self, frecuencia_id: int) -> Frecuencia:
        """Busca una frecuencia por su identificador.

        Raises:
            ValueError: Si la frecuencia no existe.
        """
        frecuencia = self._repo.obtener_por_id(frecuencia_id)
        if frecuencia is None:
            raise ValueError("Frecuencia no encontrada.")
        return frecuencia
