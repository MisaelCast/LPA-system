"""Logica de negocio para la entidad Hallazgo."""

from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.config import settings
from app.models.area import Area
from app.models.auditoria import Auditoria
from app.models.celula import Celula
from app.models.criterio import Criterio
from app.models.ejecucion_auditoria import EjecucionAuditoria
from app.models.hallazgo import ESTADOS_HALLAZGO, Hallazgo
from app.models.hallazgo_seguimiento import HallazgoSeguimiento
from app.models.respuesta import Respuesta
from app.models.usuario import Usuario
from app.repositories.hallazgo_repository import HallazgoRepository
from app.repositories.respuesta_repository import RespuestaRepository
from app.schemas.evidencia import EvidenciaOut
from app.schemas.hallazgo import (
    HallazgoCreate,
    HallazgoDetallado,
    HallazgoSeguimientoUpdate,
    HallazgoUpdate,
    ResponsableResumen,
    SeguimientoRead,
)
from app.services.area_service import AreaService
from app.services.evidencia_service import EvidenciaService, url_firmada


_VALORES_CON_HALLAZGO: set[str] = {"A", "R", "no_cumple"}
_ESTADO_FINALIZADA: str = "finalizada"
_ESTADO_CERRADO: str = "cerrado"
_ROL_RESPONSABLE: str = "Responsable de Manufactura"
_DIAS_SIN_ACTUALIZAR: int = 2
_ROLES_GESTION: set[str] = {"Supervisor", "Gerente", "Administrador"}


def _aware(valor: datetime) -> datetime:
    """Normaliza a datetime con zona horaria UTC (la BD guarda TIMESTAMP naive)."""
    if valor.tzinfo is None:
        return valor.replace(tzinfo=timezone.utc)
    return valor


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

        area_responsable_nombre: str | None = None
        if hallazgo.area_responsable_id is not None:
            area_responsable = self._session.get(
                Area, hallazgo.area_responsable_id
            )
            if area_responsable is not None:
                area_responsable_nombre = area_responsable.nombre

        evidencias = [
            EvidenciaOut(
                id=e.id or 0,
                fecha_carga=e.fecha_carga,
                tipo_archivo=e.tipo_archivo,
                tipo=e.tipo,
                url=url_firmada(e.ruta_archivo),
            )
            for e in sorted(hallazgo.evidencias, key=lambda e: e.id or 0)
        ]

        responsable = hallazgo.responsables[0] if hallazgo.responsables else None

        ahora = datetime.now(timezone.utc)
        atrasado = bool(
            hallazgo.fecha_limite is not None
            and hallazgo.estado != _ESTADO_CERRADO
            and _aware(hallazgo.fecha_limite) < ahora
        )
        seguimientos = sorted(
            hallazgo.seguimientos,
            key=lambda s: (_aware(s.fecha_creacion), s.id or 0),
        )
        ultima = (
            seguimientos[-1].fecha_creacion
            if seguimientos
            else hallazgo.fecha_creacion
        )
        dias_sin_actualizar = (ahora - _aware(ultima)).days
        reincidente = any(
            s.tipo == "cierre_rechazado" for s in seguimientos
        )

        return HallazgoDetallado(
            id=hallazgo.id,
            descripcion=hallazgo.descripcion,
            fecha_creacion=hallazgo.fecha_creacion,
            respuesta_id=hallazgo.respuesta_id,
            estado=hallazgo.estado,
            accion_correctiva=hallazgo.accion_correctiva,
            area_responsable_id=hallazgo.area_responsable_id,
            area_responsable_nombre=area_responsable_nombre,
            fecha_cierre=hallazgo.fecha_cierre,
            tipo=respuesta.valor,
            respuesta_valor=respuesta.valor,
            criterio_id=criterio.id,
            criterio_descripcion=criterio.descripcion,
            criterio_orden=criterio.orden,
            ejecucion_id=ejecucion.id,
            ejecucion_estado=ejecucion.estado,
            auditoria_id=auditoria.id if auditoria else 0,
            auditoria_nombre=auditoria.nombre if auditoria else "",
            auditor_id=ejecucion.usuario_id,
            celula_id=celula_id,
            celula_numero=celula_numero,
            evidencias=evidencias,
            fecha_limite=hallazgo.fecha_limite,
            responsable_id=responsable.id if responsable else None,
            responsable_nombre=responsable.nombre if responsable else None,
            atrasado=atrasado,
            dias_sin_actualizar=dias_sin_actualizar,
            reincidente=reincidente,
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
                "valor 'A', 'R' o 'no_cumple'."
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

        area_id = datos.area_responsable_id
        if area_id is None:
            auditoria = self._session.get(Auditoria, ejecucion.auditoria_id)
            area_id = auditoria.area_id if auditoria else None

        if area_id is None:
            raise ValueError(
                "El area responsable no existe o esta inactiva."
            )
        area = self._session.get(Area, area_id)
        if area is None or not area.activa:
            raise ValueError(
                "El area responsable no existe o esta inactiva."
            )

        responsable: Usuario | None = None
        if datos.responsable_id is not None:
            responsable = self._validar_responsable(
                datos.responsable_id, area_id
            )

        hallazgo = Hallazgo(
            descripcion=datos.descripcion,
            fecha_creacion=datetime.now(timezone.utc),
            respuesta_id=respuesta.id,
            estado="abierto",
            area_responsable_id=area_id,
        )
        guardado = self._repo.crear(hallazgo)

        if responsable is not None:
            guardado.responsables = [responsable]
            guardado.fecha_limite = datetime.now(timezone.utc) + timedelta(
                days=settings.hallazgo_plazo_dias
            )
            self._registrar(
                guardado,
                usuario,
                "asignacion",
                f"Responsable asignado: {responsable.nombre}",
            )
            guardado = self._repo.actualizar(guardado)

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

        EvidenciaService(self._session).eliminar_de_hallazgo(hallazgo)
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

    def _rol(self, usuario: Usuario) -> str:
        return getattr(getattr(usuario, "rol", None), "nombre", "")

    def _es_gestion(self, usuario: Usuario) -> bool:
        return self._rol(usuario) in _ROLES_GESTION

    def listar(
        self,
        usuario: Usuario,
        estado: str | None = None,
        area_responsable_id: int | None = None,
        solo_propios: bool = False,
        solo_auditores: bool = False,
        solo_asignados: bool = False,
        atrasados: bool = False,
        sin_actualizar: bool = False,
        cierre_pendiente: bool = False,
        reincidencia: bool = False,
    ) -> list[HallazgoDetallado]:
        """Lista hallazgos segun el rol del usuario.

        - ``solo_propios``: solo los hallazgos detectados por el propio usuario.
        - ``solo_auditores``: solo los de la capa inferior (auditores).
        - ``solo_asignados``: solo los tickets asignados al usuario como
          responsable de manufactura.
        - ``atrasados`` / ``sin_actualizar`` / ``cierre_pendiente`` /
          ``reincidencia``: filtros derivados de seguimiento (supervisores).

        Por defecto: un Auditor solo ve sus propios hallazgos; Supervisor/Gerente
        ven los de sus áreas asignadas y Administrador ve todos.
        """
        rol = self._rol(usuario)

        solo_usuario_id: int | None = None
        areas_ids: list[int] | None = None
        solo_aud = False
        solo_responsable_id: int | None = None

        if solo_asignados:
            solo_responsable_id = usuario.id
        elif solo_propios:
            solo_usuario_id = usuario.id
        elif solo_auditores:
            solo_aud = True
            if rol in ("Supervisor", "Gerente"):
                areas_ids = [a.id for a in usuario.areas] or [-1]
        else:
            solo_usuario_id = None if self._es_gestion(usuario) else usuario.id
            if rol in ("Supervisor", "Gerente"):
                areas_ids = [a.id for a in usuario.areas] or [-1]

        hallazgos = self._repo.listar(
            estado=estado,
            area_responsable_id=area_responsable_id,
            solo_usuario_id=solo_usuario_id,
            areas_ids=areas_ids,
            solo_auditores=solo_aud,
            solo_responsable_id=solo_responsable_id,
        )
        detallados = [self._enriquecer(h) for h in hallazgos]

        if atrasados:
            detallados = [h for h in detallados if h.atrasado]
        if sin_actualizar:
            detallados = [
                h
                for h in detallados
                if h.estado != _ESTADO_CERRADO
                and (h.dias_sin_actualizar or 0) >= _DIAS_SIN_ACTUALIZAR
            ]
        if cierre_pendiente:
            detallados = [
                h for h in detallados if h.estado == "cierre_solicitado"
            ]
        if reincidencia:
            detallados = [h for h in detallados if h.reincidente]
        return detallados

    def actualizar_seguimiento(
        self,
        hallazgo_id: int,
        datos: HallazgoSeguimientoUpdate,
        usuario: Usuario,
    ) -> HallazgoDetallado:
        """Actualiza estado, accion correctiva y area responsable.

        Solo el auditor que registró el hallazgo puede darle seguimiento.
        Los roles de gestion (Supervisor/Gerente/Administrador) solo pueden
        visualizarlo. No depende del estado de la ejecucion (permite cerrar
        hallazgos de ejecuciones ya finalizadas).
        """
        hallazgo = self._repo.obtener_por_id(hallazgo_id)
        if hallazgo is None:
            raise ValueError("Hallazgo no encontrado.")

        respuesta = self._obtener_respuesta(hallazgo.respuesta_id)
        ejecucion = self._obtener_ejecucion(respuesta.ejecucion_auditoria_id)

        if usuario.id != ejecucion.usuario_id:
            raise ValueError(
                "Solo el auditor que registró el hallazgo puede darle "
                "seguimiento."
            )

        if datos.estado is not None:
            if datos.estado not in ESTADOS_HALLAZGO:
                raise ValueError(
                    "Estado invalido. Debe ser abierto, en_correccion, "
                    "cierre_solicitado o cerrado."
                )
            hallazgo.estado = datos.estado
            if datos.estado == "cerrado":
                hallazgo.fecha_cierre = datetime.now(timezone.utc)
            else:
                hallazgo.fecha_cierre = None

        if datos.accion_correctiva is not None:
            hallazgo.accion_correctiva = datos.accion_correctiva

        if datos.area_responsable_id is not None:
            area = self._session.get(Area, datos.area_responsable_id)
            if area is None or not area.activa:
                raise ValueError(
                    "El area responsable no existe o esta inactiva."
                )
            hallazgo.area_responsable_id = datos.area_responsable_id

        actualizado = self._repo.actualizar(hallazgo)
        return self._enriquecer(actualizado)

    # --- Flujo de ticket: asignación, avance y cierre ---

    def _registrar(
        self,
        hallazgo: Hallazgo,
        usuario: Usuario,
        tipo: str,
        detalle: str | None = None,
        desde: str | None = None,
        hasta: str | None = None,
    ) -> None:
        """Agrega una entrada inmutable al historial del hallazgo."""
        self._session.add(
            HallazgoSeguimiento(
                hallazgo_id=hallazgo.id,
                usuario_id=usuario.id,
                tipo=tipo,
                detalle=detalle,
                estado_desde=desde,
                estado_hasta=hasta,
                fecha_creacion=datetime.now(timezone.utc),
            )
        )

    def _validar_responsable_asignado(
        self, hallazgo: Hallazgo, usuario: Usuario
    ) -> None:
        asignados = {u.id for u in hallazgo.responsables}
        if usuario.id not in asignados:
            raise ValueError(
                "Solo el responsable asignado puede actualizar este hallazgo."
            )

    def _validar_auditor_dueno(
        self, hallazgo: Hallazgo, usuario: Usuario
    ) -> EjecucionAuditoria:
        respuesta = self._obtener_respuesta(hallazgo.respuesta_id)
        ejecucion = self._obtener_ejecucion(respuesta.ejecucion_auditoria_id)
        if (
            usuario.id != ejecucion.usuario_id
            and self._rol(usuario) != "Administrador"
        ):
            raise ValueError(
                "Solo el auditor que registró el hallazgo o un administrador "
                "pueden realizar esta acción."
            )
        return ejecucion

    def _validar_responsable(
        self, responsable_id: int, area_id: int
    ) -> Usuario:
        """Valida que el usuario sea Responsable de Manufactura del area."""
        responsable = self._session.get(Usuario, responsable_id)
        if responsable is None or not responsable.activo:
            raise ValueError("El responsable no existe o esta inactivo.")
        if self._rol(responsable) != _ROL_RESPONSABLE:
            raise ValueError(
                "El usuario seleccionado no es Responsable de Manufactura."
            )
        if area_id not in {a.id for a in responsable.areas}:
            raise ValueError(
                "El responsable no pertenece al area del hallazgo."
            )
        return responsable

    def asignar_responsable(
        self,
        hallazgo_id: int,
        responsable_id: int,
        fecha_limite: datetime | None,
        usuario: Usuario,
    ) -> HallazgoDetallado:
        """Asigna o reasigna el Responsable de Manufactura de un hallazgo.

        Reglas: solo el auditor dueño (o admin); el responsable debe tener el
        rol correcto y pertenecer al área del hallazgo.
        """
        hallazgo = self._repo.obtener_por_id(hallazgo_id)
        if hallazgo is None:
            raise ValueError("Hallazgo no encontrado.")
        self._validar_auditor_dueno(hallazgo, usuario)

        if hallazgo.estado == _ESTADO_CERRADO:
            raise ValueError("No se puede reasignar un hallazgo cerrado.")
        if hallazgo.area_responsable_id is None:
            raise ValueError(
                "El hallazgo no tiene un area responsable definida."
            )

        responsable = self._validar_responsable(
            responsable_id, hallazgo.area_responsable_id
        )

        anterior = hallazgo.responsables[0] if hallazgo.responsables else None
        hallazgo.responsables = [responsable]

        if fecha_limite is not None:
            hallazgo.fecha_limite = fecha_limite
        elif hallazgo.fecha_limite is None:
            hallazgo.fecha_limite = datetime.now(timezone.utc) + timedelta(
                days=settings.hallazgo_plazo_dias
            )

        if anterior is not None and anterior.id != responsable.id:
            detalle = (
                f"Reasignado de {anterior.nombre} a {responsable.nombre}"
            )
        else:
            detalle = f"Responsable asignado: {responsable.nombre}"
        self._registrar(hallazgo, usuario, "asignacion", detalle)

        actualizado = self._repo.actualizar(hallazgo)
        return self._enriquecer(actualizado)

    def registrar_avance(
        self,
        hallazgo_id: int,
        accion_correctiva: str | None,
        comentario: str | None,
        usuario: Usuario,
    ) -> HallazgoDetallado:
        """Registra una acción correctiva/comentario del responsable.

        Transiciona ``abierto`` -> ``en_correccion`` en el primer avance.
        """
        hallazgo = self._repo.obtener_por_id(hallazgo_id)
        if hallazgo is None:
            raise ValueError("Hallazgo no encontrado.")
        self._validar_responsable_asignado(hallazgo, usuario)

        if hallazgo.estado not in ("abierto", "en_correccion"):
            raise ValueError(
                "Solo se puede registrar avance en hallazgos abiertos o en "
                "corrección."
            )

        detalle = (accion_correctiva or comentario or "").strip()
        if not detalle:
            raise ValueError(
                "Debe indicar una acción correctiva o un comentario."
            )

        desde = hallazgo.estado
        tipo = "accion_correctiva" if accion_correctiva else "comentario"
        if accion_correctiva:
            hallazgo.accion_correctiva = accion_correctiva
        if hallazgo.estado == "abierto":
            hallazgo.estado = "en_correccion"
        self._registrar(hallazgo, usuario, tipo, detalle, desde, hallazgo.estado)

        actualizado = self._repo.actualizar(hallazgo)
        return self._enriquecer(actualizado)

    def solicitar_cierre(
        self, hallazgo_id: int, comentario: str | None, usuario: Usuario
    ) -> HallazgoDetallado:
        """El responsable solicita el cierre (``en_correccion`` -> ``cierre_solicitado``)."""
        hallazgo = self._repo.obtener_por_id(hallazgo_id)
        if hallazgo is None:
            raise ValueError("Hallazgo no encontrado.")
        self._validar_responsable_asignado(hallazgo, usuario)

        if hallazgo.estado != "en_correccion":
            raise ValueError(
                "Solo se puede solicitar el cierre de un hallazgo en corrección."
            )

        desde = hallazgo.estado
        hallazgo.estado = "cierre_solicitado"
        self._registrar(
            hallazgo,
            usuario,
            "solicitud_cierre",
            comentario or "Solicitud de cierre",
            desde,
            hallazgo.estado,
        )

        actualizado = self._repo.actualizar(hallazgo)
        return self._enriquecer(actualizado)

    def resolver_cierre(
        self,
        hallazgo_id: int,
        aprobar: bool,
        observacion: str | None,
        usuario: Usuario,
    ) -> HallazgoDetallado:
        """El auditor aprueba o rechaza la solicitud de cierre.

        Rechazar devuelve el ticket a ``en_correccion`` conservando el historial.
        """
        hallazgo = self._repo.obtener_por_id(hallazgo_id)
        if hallazgo is None:
            raise ValueError("Hallazgo no encontrado.")

        if usuario.id in {u.id for u in hallazgo.responsables}:
            raise ValueError(
                "El responsable no puede aprobar el cierre de su propio "
                "hallazgo."
            )
        self._validar_auditor_dueno(hallazgo, usuario)

        if hallazgo.estado != "cierre_solicitado":
            raise ValueError(
                "El hallazgo no tiene una solicitud de cierre pendiente."
            )

        desde = hallazgo.estado
        if aprobar:
            hallazgo.estado = "cerrado"
            hallazgo.fecha_cierre = datetime.now(timezone.utc)
            tipo = "cierre_aprobado"
            detalle = observacion or "Cierre aprobado."
        else:
            hallazgo.estado = "en_correccion"
            hallazgo.fecha_cierre = None
            tipo = "cierre_rechazado"
            detalle = observacion or (
                "Cierre rechazado; se reanuda la corrección."
            )
        self._registrar(hallazgo, usuario, tipo, detalle, desde, hallazgo.estado)

        actualizado = self._repo.actualizar(hallazgo)
        return self._enriquecer(actualizado)

    def historial(
        self, hallazgo_id: int, usuario: Usuario
    ) -> list[SeguimientoRead]:
        """Devuelve el historial de seguimiento en orden cronológico."""
        hallazgo = self._repo.obtener_por_id(hallazgo_id)
        if hallazgo is None:
            raise ValueError("Hallazgo no encontrado.")
        filas = self._session.exec(
            select(HallazgoSeguimiento)
            .where(HallazgoSeguimiento.hallazgo_id == hallazgo.id)
            .order_by(
                HallazgoSeguimiento.fecha_creacion,
                HallazgoSeguimiento.id,
            )
        ).all()
        return [self._a_seguimiento_read(f) for f in filas]

    def _a_seguimiento_read(self, fila: HallazgoSeguimiento) -> SeguimientoRead:
        usuario = self._session.get(Usuario, fila.usuario_id)
        return SeguimientoRead(
            id=fila.id or 0,
            hallazgo_id=fila.hallazgo_id,
            usuario_id=fila.usuario_id,
            usuario_nombre=usuario.nombre if usuario else "",
            tipo=fila.tipo,
            detalle=fila.detalle,
            estado_desde=fila.estado_desde,
            estado_hasta=fila.estado_hasta,
            fecha_creacion=fila.fecha_creacion,
        )

    def responsables_del_area(
        self, hallazgo_id: int, usuario: Usuario
    ) -> list[ResponsableResumen]:
        """Lista los Responsables de Manufactura del área del hallazgo."""
        hallazgo = self._repo.obtener_por_id(hallazgo_id)
        if hallazgo is None:
            raise ValueError("Hallazgo no encontrado.")
        if hallazgo.area_responsable_id is None:
            return []
        return AreaService(self._session).responsables(
            hallazgo.area_responsable_id
        )