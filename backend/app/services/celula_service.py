"""Logica de negocio para la entidad Celula."""

from sqlmodel import Session, func, select

from app.models.celula import Celula
from app.repositories.celula_repository import CelulaRepository
from app.schemas.celula import CelulaCreate, CelulaUpdate


class CelulaService:
    """Servicio que encapsula la logica de negocio de celulas."""

    def __init__(self, session: Session) -> None:
        self._repo = CelulaRepository(session)
        self._session = session

    def listar_por_area(
        self, area_id: int, skip: int = 0, limit: int = 100
    ) -> list[Celula]:
        """Obtiene un listado paginado de celulas de un area."""
        return self._repo.listar_por_area(area_id, skip=skip, limit=limit)

    def obtener_por_id(self, celula_id: int) -> Celula:
        """Busca una celula por su identificador.

        Raises:
            ValueError: Si la celula no existe.
        """
        celula = self._repo.obtener_por_id(celula_id)
        if celula is None:
            raise ValueError("Celula no encontrada.")
        return celula

    def crear(self, area_id: int, datos: CelulaCreate) -> Celula:
        """Crea una celula aplicando las reglas de negocio.

        Raises:
            ValueError: Si el numero ya existe en esa area.
        """
        existente = self._repo.obtener_por_area_y_numero(
            area_id, datos.numero
        )
        if existente:
            raise ValueError(
                f"El numero de celula {datos.numero} ya existe en esta area."
            )

        celula = Celula(
            numero=datos.numero,
            activa=datos.activa,
            area_id=area_id,
        )

        return self._repo.crear(celula)

    def actualizar(self, celula_id: int, datos: CelulaUpdate) -> Celula:
        """Actualiza una celula aplicando las reglas de negocio.

        Raises:
            ValueError: Si la celula no existe o el numero ya esta en uso
                en la misma area.
        """
        celula = self.obtener_por_id(celula_id)

        if datos.numero is not None and datos.numero != celula.numero:
            existente = self._repo.obtener_por_area_y_numero(
                celula.area_id, datos.numero
            )
            if existente is not None and existente.id != celula_id:
                raise ValueError(
                    f"El numero de celula {datos.numero} ya existe en esta area."
                )

        if datos.numero is not None:
            celula.numero = datos.numero
        if datos.activa is not None:
            celula.activa = datos.activa

        return self._repo.actualizar(celula)

    def cambiar_estado(self, celula_id: int, activa: bool) -> Celula:
        """Activa o desactiva una celula.

        Raises:
            ValueError: Si la celula no existe.
        """
        celula = self.obtener_por_id(celula_id)

        if celula.activa == activa:
            return celula

        celula.activa = activa
        return self._repo.actualizar(celula)

    def eliminar(self, celula_id: int) -> None:
        """Elimina fisicamente una celula si no tiene auditorias realizadas.

        Raises:
            ValueError: Si la celula no existe o tiene ejecuciones asociadas.
        """
        from app.models.ejecucion_auditoria import EjecucionAuditoria

        celula = self.obtener_por_id(celula_id)

        total_ejecuciones = self._session.exec(
            select(func.count())
            .select_from(EjecucionAuditoria)
            .where(EjecucionAuditoria.celula_id == celula_id)
        ).one()
        if total_ejecuciones > 0:
            raise ValueError(
                "No se puede eliminar la célula porque tiene auditorías "
                "realizadas asociadas."
            )

        self._repo.eliminar(celula)
