"""Logica de negocio para la entidad Hallazgo."""

from datetime import datetime

from sqlmodel import Session, select

from app.models.auditoria import Auditoria
from app.models.celula import Celula
from app.models.criterio import Criterio
from app.models.ejecucion_auditoria import EjecucionAuditoria
from app.models.hallazgo import Hallazgo
from app.models.respuesta import Respuesta
from app.models.usuario import Usuario
from app.repositories.hallazgo_repository import HallazgoRepository
from app.repositories.respuesta_repository import RespuestaRepository
from app.schemas.hallazgo import HallazgoCreate, HallazgoDetallado, HallazgoUpdate


_VALORES_CON_HALLAZGO: set[str] = {"A", "R"}
_ESTADO_FINALIZADA: str = "finalizada"


class HallazgoService:
    """Servicio que encapsula las reglas de dominio de los hallazgos."""

    def __init__(self, session: Session) -> None:
        self._repo = HallazgoRepository(session)
        self._respuesta_repo = RespuestaRepository(session)
        self._session = session

    def _obtener_respuesta(self, respuesta_id: int) -> Respuesta:
        respuesta = self._respuesta_repo.obtener_por_id(respuesta_id)
        if respuesta is None:
            raise ValueError("Respuesta no encontrada.")
        return respuesta

    def _obtener_ejecucion(self, ejecucion_id: int) -> EjecucionAuditoria:
        ejecucion = self._session.get(EjecucionAuditoria, ejecucion_id)
        if ejecucion is None:
            raise ValueError("Ejecucion de auditoria no encontrada.")
        return ejecucion

    def _enriquecer(self, hallazgo: Hallazgo) -> HallazgoDetallado:
        respuesta = self._respuesta_repo.obtener_por_id(hallazgo.respuesta_id)
        if respuesta is None:
            raise ValueError(
                "La respuesta asociada al hallazgo no existe."
            )

        criterio = self._session.get(Criterio, respuesta.criterio_id)
        if criterio is None:
            raise ValueError(
                "El criterio asociado a la respuesta no existe."
            )

        ejecucion = self._session.get(EjecucionAuditoria, respuesta.ejecucion_auditoria_id)
        if ejecucion is None:
            raise ValueError(
                "La ejecucion asociada a la respuesta no existe."
            )

        auditoria = self._session.get(Auditoria, ejecucion.auditoria_id)
        celula_id = ejecucion.celula_id
        celula_numero: int | None = None
        if celula_id is not None:
            celula = self._session.get(Celula, celula_id)
            if celula is not None:
                celula_numero = celula.numero

        return HallazgoDetallado(
            id=hallazgo.id,
            descripcion=hallazgo.descripcion,
            fecha_creacion=hallazgo.fecha_creacion,
            respuesta_id=hallazgo.respuesta_id,
            tipo=respuesta.valor,
            respuesta_valor=respuesta.valor,
            criterio_id=criterio.id,
            criterio_descripcion=criterio.descripcion,
            criterio_orden=criterio.orden,
            ejecucion_id=ejecucion.id,
            ejecucion_estado=ejecucion.estado,
            auditoria_id=auditoria.id if auditoria else 0,
            auditoria_nombre=auditoria.nombre if auditoria else "",
            celula_id=celula_id,
            celula_numero=celula_numero,
        )

    def crear(self, datos: HallazgoCreate, usuario: Usuario) -> HallazgoDetallado:
        """Crea un hallazgo para la respuesta indicada.

        Reglas:
        - La respuesta debe existir.
        - La ejecucion debe existir y no estar finalizada.
        - El usuario debe tener permiso sobre la ejecucion.
        - La respuesta debe tener valor ``A`` o ``R``.
        - No debe existir un hallazgo previo para la misma respuesta.
        """
        respuesta = self._obtener_respuesta(datos.respuesta_id)
        ejecucion = self._obtener_ejecucion(respuesta.ejecucion_auditoria_id)

        if ejecucion.estado == _ESTADO_FINALIZADA:
            raise ValueError(
                "No se pueden crear hallazgos en una ejecucion finalizada."
            )

        if usuario.id != ejecucion.usuario_id:
            rol_nombre = getattr(usuario.rol, "nombre", "")
            if rol_nombre != "Administrador":
                raise ValueError(
                    "Solo el auditor asignado o un administrador pueden "
                    "registrar hallazgos en esta ejecucion."
                )

        if respuesta.valor not in _VALORES_CON_HALLAZGO:
            raise ValueError(
                "Solo se pueden crear hallazgos para respuestas con "
                "valor 'A' o 'R'."
            )

        criterio = self._session.get(Criterio, respuesta.criterio_id)
        if criterio is None:
            raise ValueError("El criterio de la respuesta no existe.")
        if criterio.auditoria_id != ejecucion.auditoria_id:
            raise ValueError(
                "El criterio no pertenece a la auditoria de la ejecucion."
            )

        existente = self._repo.obtener_por_respuesta(respuesta.id)
        if existente is not None:
            raise ValueError(
                "Ya existe un hallazgo registrado para esta respuesta."
            )

        hallazgo = Hallazgo(
            descripcion=datos.descripcion,
            fecha_creacion=datetime.utcnow(),
            respuesta_id=respuesta.id,
        )
        guardado = self._repo.crear(hallazgo)
        return self._enriquecer(guardado)

    def obtener_por_id(self, hallazgo_id: int) -> HallazgoDetallado:
        hallazgo = self._repo.obtener_por_id(hallazgo_id)
        if hallazgo is None:
            raise ValueError("Hallazgo no encontrado.")
        return self._enriquecer(hallazgo)

    def actualizar(
        self, hallazgo_id: int, datos: HallazgoUpdate, usuario: Usuario
    ) -> HallazgoDetallado:
        hallazgo = self._repo.obtener_por_id(hallazgo_id)
        if hallazgo is None:
            raise ValueError("Hallazgo no encontrado.")

        respuesta = self._obtener_respuesta(hallazgo.respuesta_id)
        ejecucion = self._obtener_ejecucion(respuesta.ejecucion_auditoria_id)

        if ejecucion.estado == _ESTADO_FINALIZADA:
            raise ValueError(
                "No se puede modificar un hallazgo de una ejecucion finalizada."
            )

        if usuario.id != ejecucion.usuario_id:
            rol_nombre = getattr(usuario.rol, "nombre", "")
            if rol_nombre != "Administrador":
                raise ValueError(
                    "Solo el auditor asignado o un administrador pueden "
                    "modificar este hallazgo."
                )

        if datos.descripcion is not None:
            hallazgo.descripcion = datos.descripcion

        actualizado = self._repo.actualizar(hallazgo)
        return self._enriquecer(actualizado)

    def eliminar(self, hallazgo_id: int, usuario: Usuario) -> None:
        """Eliminacion controlada del hallazgo.

        Solo permitida mientras la ejecucion este en proceso y el usuario
        sea el auditor asignado o un administrador.
        """
        hallazgo = self._repo.obtener_por_id(hallazgo_id)
        if hallazgo is None:
            raise ValueError("Hallazgo no encontrado.")

        respuesta = self._obtener_respuesta(hallazgo.respuesta_id)
        ejecucion = self._obtener_ejecucion(respuesta.ejecucion_auditoria_id)

        if ejecucion.estado == _ESTADO_FINALIZADA:
            raise ValueError(
                "No se puede eliminar un hallazgo de una ejecucion finalizada."
            )

        if usuario.id != ejecucion.usuario_id:
            rol_nombre = getattr(usuario.rol, "nombre", "")
            if rol_nombre != "Administrador":
                raise ValueError(
                    "Solo el auditor asignado o un administrador pueden "
                    "eliminar este hallazgo."
                )

        self._repo.eliminar(hallazgo)

    def listar_por_ejecucion(
        self, ejecucion_id: int, usuario: Usuario
    ) -> list[HallazgoDetallado]:
        """Devuelve los hallazgos de una ejecucion ordenados por criterio.orden."""
        ejecucion = self._obtener_ejecucion(ejecucion_id)

        if (
            usuario.id != ejecucion.usuario_id
            and getattr(usuario.rol, "nombre", "") != "Administrador"
        ):
            raise ValueError(
                "No tiene permiso para consultar los hallazgos de esta ejecucion."
            )

        hallazgos = self._repo.listar_por_ejecucion(ejecucion_id)
        detallados = [self._enriquecer(h) for h in hallazgos]
        detallados.sort(key=lambda h: (h.criterio_orden, h.id))
        return detallados