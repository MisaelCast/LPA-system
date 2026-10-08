"""Logica de negocio para EjecucionAuditoria y Respuesta."""

from datetime import datetime, timedelta, timezone

from sqlmodel import Session, func, select

from app.models.area import Area
from app.models.auditoria import Auditoria
from app.models.capa import Capa
from app.models.celula import Celula
from app.models.criterio import Criterio
from app.models.ejecucion_auditoria import EjecucionAuditoria
from app.models.frecuencia import Frecuencia
from app.models.hallazgo import Hallazgo
from app.models.respuesta import Respuesta
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.models.usuario_celula import UsuarioCelula
from app.repositories.ejecucion_auditoria_repository import (
    EjecucionAuditoriaRepository,
)
from app.repositories.respuesta_repository import RespuestaRepository
from app.services.programacion_service import (
    _crear_pendiente,
    fecha_habilita,
    marcar_no_elaboradas,
    periodo_auditoria,
    siguiente_habilita,
)
from app.utils.tiempo import ahora_business

_VALORES_POR_TIPO_RESPUESTA: dict[str, set[str]] = {
    "semaforo": {"V", "A", "R"},
    "cumplimiento": {"cumple", "no_cumple", "na"},
}

_ESTADOS_VALIDOS: tuple[str, ...] = (
    "pendiente",
    "en_proceso",
    "finalizada",
    "vencida",
    "no_elaborada",
)


class DiaNoHabilitadoError(ValueError):
    """Se intenta iniciar una auditoría antes de su día habilitado (403)."""


class EjecucionAbiertaError(ValueError):
    """Ya existe una ejecución abierta para el mismo periodo (409)."""


_NOMBRES_DIA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


class EjecucionAuditoriaService:
    """Servicio que encapsula la logica de negocio de ejecuciones de auditoria."""

    def __init__(self, session: Session) -> None:
        self._repo = EjecucionAuditoriaRepository(session)
        self._respuesta_repo = RespuestaRepository(session)
        self._session = session

    def _dias_frecuencia_de_auditoria(self, auditoria_id: int) -> int | None:
        auditoria = self._session.get(Auditoria, auditoria_id)
        if auditoria is None:
            return None
        frecuencia = self._session.get(Frecuencia, auditoria.frecuencia_id)
        return frecuencia.dias if frecuencia else None

    def _programacion_de_ejecucion(
        self, ejecucion: EjecucionAuditoria
    ) -> dict:
        """Calcula fecha_limite, programada y vencida de una ejecución.

        ``vencida`` es derivado: una ejecución ``pendiente`` cuya fecha límite
        (programada + frecuencia.dias) ya pasó.
        """
        programada = isinstance(ejecucion.fecha_programada, datetime)
        fecha_limite: datetime | None = None
        vencida = False

        fecha_programada = ejecucion.fecha_programada
        if isinstance(fecha_programada, datetime) and fecha_programada.tzinfo is None:
            fecha_programada = fecha_programada.replace(tzinfo=timezone.utc)

        if programada:
            dias = self._dias_frecuencia_de_auditoria(ejecucion.auditoria_id)
            if dias:
                fecha_limite = fecha_programada + timedelta(days=dias)
                if (
                    ejecucion.estado == "pendiente"
                    and datetime.now(timezone.utc) > fecha_limite
                ):
                    vencida = True

        return {
            "fecha_programada": fecha_programada,
            "fecha_limite": fecha_limite,
            "programada": programada,
            "vencida": vencida,
        }

    def _enriquecer_read(
        self, ejecucion: EjecucionAuditoria
    ) -> EjecucionAuditoria:
        object.__setattr__(ejecucion, "auditoria_nombre", "")
        object.__setattr__(ejecucion, "area_nombre", "")
        object.__setattr__(ejecucion, "celula_numero", None)
        object.__setattr__(ejecucion, "auditor_nombre", "")
        object.__setattr__(ejecucion, "tipo_respuesta", "semaforo")

        auditoria = self._session.get(Auditoria, ejecucion.auditoria_id)
        if auditoria:
            object.__setattr__(ejecucion, "auditoria_nombre", auditoria.nombre)
            object.__setattr__(
                ejecucion, "tipo_respuesta", auditoria.tipo_respuesta
            )
            if auditoria.area_id:
                from app.models.area import Area

                area = self._session.get(Area, auditoria.area_id)
                if area:
                    object.__setattr__(ejecucion, "area_nombre", area.nombre)

        programacion = self._programacion_de_ejecucion(ejecucion)
        object.__setattr__(
            ejecucion, "fecha_programada", programacion["fecha_programada"]
        )
        object.__setattr__(ejecucion, "fecha_limite", programacion["fecha_limite"])
        object.__setattr__(ejecucion, "programada", programacion["programada"])
        object.__setattr__(ejecucion, "vencida", programacion["vencida"])

        if ejecucion.celula_id:
            celula = self._session.get(Celula, ejecucion.celula_id)
            if celula:
                object.__setattr__(ejecucion, "celula_numero", celula.numero)

        usuario = self._session.get(Usuario, ejecucion.usuario_id)
        if usuario:
            object.__setattr__(ejecucion, "auditor_nombre", usuario.nombre)

        respuestas = self._respuesta_repo.listar_por_ejecucion(ejecucion.id)

        respuestas_por_id = {r.id: r for r in respuestas}

        hallazgos = list(
            self._session.exec(
                select(Hallazgo).where(
                    Hallazgo.respuesta_id.in_(
                        list(respuestas_por_id.keys())
                    )
                    if respuestas_por_id
                    else Hallazgo.id == -1
                )
            ).all()
        )
        hallazgo_por_respuesta = {h.respuesta_id: h for h in hallazgos}

        criterios = (
            self._session.exec(
                select(Criterio)
                .where(Criterio.auditoria_id == ejecucion.auditoria_id)
                .where(Criterio.activo == True)
                .order_by(Criterio.orden)
            ).all()
        )

        criterios_enriquecidos: list[dict] = []
        for criterio in criterios:
            respuesta = next(
                (r for r in respuestas if r.criterio_id == criterio.id),
                None,
            )
            hallazgo = (
                hallazgo_por_respuesta.get(respuesta.id)
                if respuesta is not None
                else None
            )
            criterios_enriquecidos.append({
                "id": criterio.id,
                "descripcion": criterio.descripcion,
                "orden": criterio.orden,
                "seccion": criterio.seccion,
                "subseccion": criterio.subseccion,
                "subtitulo": criterio.subtitulo,
                "respuesta_valor": respuesta.valor if respuesta else None,
                "respuesta_observaciones": (
                    respuesta.observaciones if respuesta else None
                ),
                "respuesta_id": respuesta.id if respuesta else None,
                "hallazgo_id": hallazgo.id if hallazgo else None,
                "hallazgo_descripcion": (
                    hallazgo.descripcion if hallazgo else None
                ),
            })

        object.__setattr__(ejecucion, "criterios", criterios_enriquecidos)

        return ejecucion

    def listar_disponibles(self, usuario: Usuario) -> list[Auditoria]:
        query = select(Auditoria).where(Auditoria.activa == True)  # noqa: E712

        rol_nombre = getattr(getattr(usuario, "rol", None), "nombre", "")
        if rol_nombre in ("Auditor", "Supervisor", "Gerente"):
            from app.models.capa import Capa

            capa = self._session.exec(
                select(Capa).where(Capa.nombre == rol_nombre)
            ).first()
            if capa is not None:
                query = query.where(Auditoria.capa_id == capa.id)

            # Restringe a las áreas asignadas del usuario.
            areas_ids = [a.id for a in usuario.areas]
            if areas_ids:
                query = query.where(Auditoria.area_id.in_(areas_ids))
            else:
                query = query.where(Auditoria.id == -1)

        auditorias = list(self._session.exec(query).all())
        return [self._enriquecer_auditoria(a) for a in auditorias]

    def _enriquecer_auditoria(self, auditoria: Auditoria) -> Auditoria:
        object.__setattr__(auditoria, "capa_nombre", "")
        object.__setattr__(auditoria, "frecuencia_nombre", "")
        object.__setattr__(auditoria, "area_nombre", None)
        object.__setattr__(auditoria, "requiere_celula", True)

        if auditoria.capa_id is not None:
            from app.models.capa import Capa
            capa = self._session.get(Capa, auditoria.capa_id)
            if capa:
                object.__setattr__(auditoria, "capa_nombre", capa.nombre)
                object.__setattr__(auditoria, "requiere_celula", capa.requiere_celula)

        if auditoria.frecuencia_id is not None:
            from app.models.frecuencia import Frecuencia
            frecuencia = self._session.get(Frecuencia, auditoria.frecuencia_id)
            if frecuencia:
                object.__setattr__(auditoria, "frecuencia_nombre", frecuencia.nombre)

        if auditoria.area_id is not None:
            from app.models.area import Area
            area = self._session.get(Area, auditoria.area_id)
            if area:
                object.__setattr__(auditoria, "area_nombre", area.nombre)

        return auditoria

    def obtener_celulas_disponibles(
        self, auditoria_id: int, usuario: Usuario
    ) -> list[Celula]:
        auditoria = self._session.get(Auditoria, auditoria_id)
        if auditoria is None:
            raise ValueError("Auditoria no encontrada.")
        if not auditoria.activa:
            raise ValueError("La auditoria no esta activa.")

        if auditoria.area_id is None:
            return list(
                self._session.exec(
                    select(Celula).where(Celula.activa == True)
                ).all()
            )

        query = select(Celula).where(
            Celula.area_id == auditoria.area_id,
            Celula.activa == True,  # noqa: E712
        )

        # Si el usuario tiene células a cargo, se limita a esas.
        celulas_ids = [c.id for c in usuario.celulas]
        if celulas_ids:
            query = query.where(Celula.id.in_(celulas_ids))

        return list(self._session.exec(query).all())

    def iniciar(
        self, auditoria_id: int, usuario: Usuario, celula_id: int | None = None
    ) -> EjecucionAuditoria:
        auditoria = self._session.get(Auditoria, auditoria_id)
        if auditoria is None:
            raise ValueError("Auditoria no encontrada.")
        if not auditoria.activa:
            raise ValueError("La auditoria no esta activa.")

        capa = (
            self._session.get(Capa, auditoria.capa_id)
            if auditoria.capa_id
            else None
        )
        requiere_celula = capa.requiere_celula if capa else True

        if not requiere_celula:
            celula_id = None  # la capa no requiere célula
        else:
            if celula_id is None:
                raise ValueError("Esta auditoría requiere seleccionar una célula.")
            celula = self._session.get(Celula, celula_id)
            if celula is None:
                raise ValueError("Celula no encontrada.")
            if not celula.activa:
                raise ValueError("La celula no esta activa.")
            if auditoria.area_id is not None and celula.area_id != auditoria.area_id:
                raise ValueError(
                    "La celula no pertenece al area de la auditoria."
                )

        self._validar_habilitacion(auditoria)
        periodo = periodo_auditoria(
            auditoria, self._frecuencia_de(auditoria), ahora_business()
        )
        pendiente = self._session.exec(
            select(EjecucionAuditoria).where(
                EjecucionAuditoria.auditoria_id == auditoria.id,
                EjecucionAuditoria.celula_id == celula_id,
                EjecucionAuditoria.usuario_id == usuario.id,
                EjecucionAuditoria.fecha_programada == periodo,
                EjecucionAuditoria.estado == "pendiente",
            )
        ).first()
        if pendiente is not None:
            # Ya existe la pendiente programada del periodo: se retoma en vez
            # de crear otra ni rechazar con 409 (inicio desde Ejecutar).
            pendiente.estado = "en_proceso"
            pendiente.fecha = datetime.now(timezone.utc)
            self._repo.actualizar(pendiente)
            return pendiente
        self._validar_sin_abierta(auditoria, usuario, celula_id)

        ejecucion = EjecucionAuditoria(
            fecha=datetime.now(timezone.utc),
            fecha_programada=periodo_auditoria(
                auditoria,
                self._frecuencia_de(auditoria),
            ),
            estado="en_proceso",
            auditoria_id=auditoria.id,
            usuario_id=usuario.id,
            celula_id=celula_id,
        )
        return self._repo.crear(ejecucion)

    def _frecuencia_de(self, auditoria: Auditoria) -> Frecuencia | None:
        return (
            self._session.get(Frecuencia, auditoria.frecuencia_id)
            if auditoria.frecuencia_id
            else None
        )

    def _validar_habilitacion(self, auditoria: Auditoria) -> None:
        """Rechaza iniciar una auditoría antes de su día habilitado (403)."""
        if auditoria.dia_semana is None:
            return
        frecuencia = self._frecuencia_de(auditoria)
        habilita = fecha_habilita(auditoria, frecuencia, ahora_business())
        if habilita is not None and ahora_business() < habilita:
            dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            nombre_dia = dias[auditoria.dia_semana]
            raise DiaNoHabilitadoError(
                f"Esta auditoría se habilita solo los {nombre_dia}. "
                f"Se habilita el día {habilita.strftime('%d/%m/%Y')}."
            )

    def _validar_sin_abierta(
        self,
        auditoria: Auditoria,
        usuario: Usuario,
        celula_id: int | None,
        periodo: datetime | None = None,
        excluir_ejecucion_id: int | None = None,
    ) -> None:
        """Rechaza si ya hay una ejecución abierta del mismo periodo (409)."""
        frecuencia = self._frecuencia_de(auditoria)
        periodo = periodo or periodo_auditoria(auditoria, frecuencia, ahora_business())
        query = select(EjecucionAuditoria).where(
            EjecucionAuditoria.auditoria_id == auditoria.id,
            EjecucionAuditoria.celula_id == celula_id,
            EjecucionAuditoria.usuario_id == usuario.id,
            EjecucionAuditoria.fecha_programada == periodo,
            EjecucionAuditoria.estado.in_(("pendiente", "en_proceso")),
        )
        if excluir_ejecucion_id is not None:
            query = query.where(EjecucionAuditoria.id != excluir_ejecucion_id)
        if self._session.exec(query).first() is not None:
            raise EjecucionAbiertaError(
                "Ya existe una ejecución abierta de esta auditoría "
                "para el mismo periodo."
            )

    def obtener_por_id(self, ejecucion_id: int) -> EjecucionAuditoria:
        ejecucion = self._repo.obtener_por_id(ejecucion_id)
        if ejecucion is None:
            raise ValueError("Ejecucion de auditoria no encontrada.")
        return self._enriquecer_read(ejecucion)

    def _es_admin(self, usuario: Usuario) -> bool:
        rol = getattr(usuario, "rol", None)
        return getattr(rol, "nombre", "") == "Administrador"

    def _es_supervisor(self, usuario: Usuario) -> bool:
        rol = getattr(usuario, "rol", None)
        return getattr(rol, "nombre", "") == "Supervisor"

    def _es_gerente(self, usuario: Usuario) -> bool:
        rol = getattr(usuario, "rol", None)
        return getattr(rol, "nombre", "") == "Gerente"

    def _validar_puede_modificar(
        self, ejecucion: EjecucionAuditoria, usuario: Usuario
    ) -> None:
        """Garantiza que solo el auditor asignado o un administrador modifiquen.

        Evita que un supervisor (u otro rol) altere la auditoría original.
        """
        if usuario.id == ejecucion.usuario_id:
            return
        if self._es_admin(usuario):
            return
        raise ValueError(
            "Solo el auditor asignado o un administrador pueden "
            "modificar esta ejecución."
        )

    def _resumen_de_respuestas(
        self, respuestas: list[Respuesta], total_criterios: int
    ) -> dict:
        total_v = sum(1 for r in respuestas if r.valor == "V")
        total_a = sum(1 for r in respuestas if r.valor == "A")
        total_r = sum(1 for r in respuestas if r.valor == "R")
        total_cumple = sum(1 for r in respuestas if r.valor == "cumple")
        total_no_cumple = sum(1 for r in respuestas if r.valor == "no_cumple")
        total_na = sum(1 for r in respuestas if r.valor == "na")
        return {
            "total_criterios": total_criterios,
            "total_v": total_v,
            "total_a": total_a,
            "total_r": total_r,
            "total_cumple": total_cumple,
            "total_no_cumple": total_no_cumple,
            "total_na": total_na,
        }

    def _contar_criterios_activos(self, auditoria_id: int) -> int:
        return self._session.exec(
            select(func.count()).select_from(Criterio).where(
                Criterio.auditoria_id == auditoria_id,
                Criterio.activo == True,  # noqa: E712
            )
        ).one()

    def _valores_permitidos_por_auditoria(
        self, auditoria: Auditoria | None
    ) -> set[str]:
        tipo = auditoria.tipo_respuesta if auditoria else "semaforo"
        return _VALORES_POR_TIPO_RESPUESTA.get(tipo, _VALORES_POR_TIPO_RESPUESTA["semaforo"])

    def _a_list_item(
        self, ejecucion: EjecucionAuditoria, respuestas: list[Respuesta]
    ) -> dict:
        auditoria_nombre = ""
        area_id: int | None = None
        area_nombre: str | None = None
        tipo_respuesta = "semaforo"

        auditoria = self._session.get(Auditoria, ejecucion.auditoria_id)
        if auditoria:
            auditoria_nombre = auditoria.nombre
            tipo_respuesta = auditoria.tipo_respuesta
            if auditoria.area_id:
                area_id = auditoria.area_id
                area = self._session.get(Area, auditoria.area_id)
                if area:
                    area_nombre = area.nombre

        celula_numero: int | None = None
        if ejecucion.celula_id:
            celula = self._session.get(Celula, ejecucion.celula_id)
            if celula:
                celula_numero = celula.numero

        usuario_nombre = ""
        usuario = self._session.get(Usuario, ejecucion.usuario_id)
        if usuario:
            usuario_nombre = usuario.nombre

        total_criterios = self._contar_criterios_activos(ejecucion.auditoria_id)
        programacion = self._programacion_de_ejecucion(ejecucion)

        return {
            "id": ejecucion.id,
            "fecha": ejecucion.fecha,
            "estado": ejecucion.estado,
            "auditoria_id": ejecucion.auditoria_id,
            "auditoria_nombre": auditoria_nombre,
            "usuario_id": ejecucion.usuario_id,
            "usuario_nombre": usuario_nombre,
            "celula_id": ejecucion.celula_id,
            "celula_numero": celula_numero,
            "area_id": area_id,
            "area_nombre": area_nombre,
            "tipo_respuesta": tipo_respuesta,
            "fecha_programada": programacion["fecha_programada"],
            "fecha_limite": programacion["fecha_limite"],
            "programada": programacion["programada"],
            "vencida": programacion["vencida"],
            "resumen": self._resumen_de_respuestas(respuestas, total_criterios),
        }

    def listar_ejecuciones(
        self,
        usuario: Usuario,
        skip: int = 0,
        limit: int = 100,
        auditoria_id: int | None = None,
        celula_id: int | None = None,
        usuario_id: int | None = None,
        estado: str | None = None,
        fecha_desde: datetime | None = None,
        fecha_hasta: datetime | None = None,
        area_id: int | None = None,
        tipo_respuesta: str | None = None,
        solo_auditores: bool = False,
        solo_propias: bool = False,
    ) -> list[dict]:
        """Lista las ejecuciones del historial con sus resumenes V/A/R.

        Un auditor solo ve sus propias ejecuciones; un supervisor o gerente ve
        todas y un administrador ve todas salvo que se indique ``solo_propias``,
        en cuyo caso se limita a las propias (vista "Auditorías realizadas").

        Los **Supervisores y Gerentes** además se restringen a sus áreas
        asignadas: no ven ejecuciones de áreas ajenas.
        """
        areas_ids: list[int] | None = None
        if self._es_supervisor(usuario) or self._es_gerente(usuario):
            areas_ids = [a.id for a in usuario.areas]
            if not areas_ids:
                areas_ids = [-1]  # sin áreas asignadas → no ve nada

        if solo_propias:
            usuario_id = usuario.id
        elif not (
            self._es_admin(usuario)
            or self._es_supervisor(usuario)
            or self._es_gerente(usuario)
        ):
            usuario_id = usuario.id

        ejecuciones = self._repo.listar_con_filtros(
            skip=skip,
            limit=limit,
            auditoria_id=auditoria_id,
            celula_id=celula_id,
            usuario_id=usuario_id,
            estado=estado,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            area_id=area_id,
            areas_ids=areas_ids,
            tipo_respuesta=tipo_respuesta,
            solo_auditores=solo_auditores,
        )

        respuestas_por_ejecucion: dict[int, list[Respuesta]] = {}
        if ejecuciones:
            ids = [e.id for e in ejecuciones]
            respuestas = list(
                self._session.exec(
                    select(Respuesta).where(
                        Respuesta.ejecucion_auditoria_id.in_(ids)
                    )
                ).all()
            )
            for r in respuestas:
                respuestas_por_ejecucion.setdefault(
                    r.ejecucion_auditoria_id, []
                ).append(r)

        return [
            self._a_list_item(
                e, respuestas_por_ejecucion.get(e.id, [])
            )
            for e in ejecuciones
        ]

    def obtener_opciones_filtros(self, usuario: Usuario) -> dict:
        """Devuelve las opciones de filtro para la revisión de auditorías.

        Útil para poblar los selectores de área, célula y auditor de la vista
        de revisión (Supervisor/Gerente/Administrador). Un Supervisor o Gerente
        solo ve las áreas que tiene asignadas.
        """
        areas_query = select(Area).where(Area.activa == True)  # noqa: E712
        if self._es_supervisor(usuario) or self._es_gerente(usuario):
            areas_ids = [a.id for a in usuario.areas]
            areas_query = areas_query.where(
                Area.id.in_(areas_ids) if areas_ids else Area.id == -1
            )
        areas = list(
            self._session.exec(
                areas_query.order_by(Area.nombre)
            ).all()
        )
        celulas = list(
            self._session.exec(
                select(Celula)
                .where(Celula.activa == True)  # noqa: E712
                .order_by(Celula.area_id, Celula.numero)
            ).all()
        )
        auditores = list(
            self._session.exec(
                select(Usuario)
                .join(Rol, Usuario.rol_id == Rol.id)
                .where(Rol.nombre == "Auditor", Usuario.activo == True)  # noqa: E712
                .order_by(Usuario.nombre)
            ).all()
        )

        return {
            "areas": areas,
            "celulas": celulas,
            "auditores": auditores,
        }

    def obtener_detalle(self, ejecucion_id: int) -> dict:
        """Devuelve el detalle completo de una ejecucion con resumen V/A/R."""
        ejecucion = self.obtener_por_id(ejecucion_id)

        respuestas = self._respuesta_repo.listar_por_ejecucion(ejecucion_id)
        total_criterios = self._contar_criterios_activos(ejecucion.auditoria_id)

        area_id: int | None = None
        auditoria = self._session.get(Auditoria, ejecucion.auditoria_id)
        if auditoria and auditoria.area_id:
            area_id = auditoria.area_id

        programacion = self._programacion_de_ejecucion(ejecucion)

        return {
            "id": ejecucion.id,
            "fecha": ejecucion.fecha,
            "observaciones": getattr(ejecucion, "observaciones", None),
            "estado": ejecucion.estado,
            "auditoria_id": ejecucion.auditoria_id,
            "usuario_id": ejecucion.usuario_id,
            "celula_id": ejecucion.celula_id,
            "auditoria_nombre": getattr(ejecucion, "auditoria_nombre", ""),
            "area_nombre": getattr(ejecucion, "area_nombre", None),
            "celula_numero": getattr(ejecucion, "celula_numero", None),
            "auditor_nombre": getattr(ejecucion, "auditor_nombre", ""),
            "area_id": area_id,
            "tipo_respuesta": getattr(ejecucion, "tipo_respuesta", "semaforo"),
            "fecha_programada": programacion["fecha_programada"],
            "fecha_limite": programacion["fecha_limite"],
            "programada": programacion["programada"],
            "vencida": programacion["vencida"],
            "criterios": getattr(ejecucion, "criterios", []),
            "resumen": self._resumen_de_respuestas(respuestas, total_criterios),
        }

    def mis_pendientes(self, usuario: Usuario) -> list[dict]:
        """Lista las auditorías programadas del usuario con su estado.

        - Diarias (lunes a viernes): se generan por día hábil; la del día se
          habilita ese día y, si no fue finalizada antes de terminar el día,
          queda registrada como ``no_elaborada`` y sale la del siguiente día.
        - Semanales con ``dia_semana``: Bloqueada (antes del día), Disponible
          (el día) o Atrasada (después); se generan al consultar.
        - De proceso (sin día): Disponible/Atrasada según periodo y En progreso
          si iniciadas.
        """
        ahora = ahora_business()
        marcadas = marcar_no_elaboradas(self._session, ahora)
        if marcadas:
            self._session.commit()
        items: list[dict] = []
        for auditoria in self.listar_disponibles(usuario):
            frecuencia = self._frecuencia_de(auditoria)
            if frecuencia is None:
                continue
            if auditoria.tipo_respuesta == "cumplimiento":
                item = self._pendiente_item(
                    usuario, auditoria, frecuencia, None, ahora
                )
                if item is not None:
                    items.append(item)
            else:
                for celula in self.obtener_celulas_disponibles(
                    auditoria.id, usuario
                ):
                    item = self._pendiente_item(
                        usuario, auditoria, frecuencia, celula.id, ahora
                    )
                    if item is not None:
                        items.append(item)

        orden_estado = {
            "atrasada": 0,
            "en_progreso": 1,
            "disponible": 2,
            "bloqueada": 3,
        }
        items.sort(key=lambda i: (orden_estado[i["estado"]], -i["dias"]))
        return items

    def _pendiente_item(
        self,
        usuario: Usuario,
        auditoria: Auditoria,
        frecuencia: Frecuencia,
        celula_id: int | None,
        ahora: datetime,
    ) -> dict | None:
        area_nombre = None
        if auditoria.area_id:
            area = self._session.get(Area, auditoria.area_id)
            area_nombre = area.nombre if area else None
        celula_numero = None
        if celula_id is not None:
            celula = self._session.get(Celula, celula_id)
            celula_numero = celula.numero if celula else None

        def _base(estado: str, dias: int, contador: str | None,
                  ejecucion_id: int | None, accion: str | None,
                  habilita: datetime | None) -> dict:
            return {
                "ejecucion_id": ejecucion_id,
                "auditoria_id": auditoria.id,
                "auditoria_nombre": auditoria.nombre,
                "area_nombre": area_nombre,
                "celula_numero": celula_numero,
                "estado": estado,
                "fecha_habilita": habilita,
                "contador": contador,
                "dias": dias,
                "accion": accion,
                "tooltip": (
                    (
                        f"Se habilita el {_NOMBRES_DIA[auditoria.dia_semana]} "
                        f"{habilita.strftime('%d/%m/%Y')}."
                        if auditoria.dia_semana is not None
                        else f"Se habilita el {habilita.strftime('%d/%m/%Y')}."
                    )
                    if habilita is not None
                    else None
                ),
                "requiere_celula": getattr(auditoria, "requiere_celula", True),
            }

        habilita = fecha_habilita(auditoria, frecuencia, ahora)
        if habilita is not None:
            dias_rel = (ahora.date() - habilita.date()).days
            if dias_rel < 0:
                faltan = -dias_rel
                contador = "Mañana" if faltan == 1 else f"Faltan {faltan} días"
                return _base("bloqueada", -faltan, contador, None, None, habilita)

        periodo = periodo_auditoria(auditoria, frecuencia, ahora)
        ejecucion = self._session.exec(
            select(EjecucionAuditoria).where(
                EjecucionAuditoria.auditoria_id == auditoria.id,
                EjecucionAuditoria.celula_id == celula_id,
                EjecucionAuditoria.usuario_id == usuario.id,
                EjecucionAuditoria.fecha_programada == periodo,
            )
        ).first()

        if ejecucion is not None and ejecucion.estado == "en_proceso":
            return _base("en_progreso", 0, "En progreso",
                         ejecucion.id, "continuar", habilita)

        if (
            ejecucion is not None
            and ejecucion.estado in ("finalizada", "no_elaborada")
        ):
            # Periodo completado: el ítem ya no aparece como disponible;
            # se anticipa la siguiente ocurrencia como bloqueada (o
            # desaparece si la auditoría no tiene día fijo).
            sig = siguiente_habilita(auditoria, frecuencia, habilita)
            if sig is None:
                return None
            faltan = (sig.date() - ahora.date()).days
            return _base(
                "bloqueada",
                -faltan,
                "Mañana" if faltan == 1 else f"Faltan {faltan} días",
                None,
                None,
                sig,
            )

        if ejecucion is None:
            _crear_pendiente(
                self._session, auditoria.id, celula_id, usuario.id, periodo
            )
            self._session.commit()
            ejecucion = self._session.exec(
                select(EjecucionAuditoria).where(
                    EjecucionAuditoria.auditoria_id == auditoria.id,
                    EjecucionAuditoria.celula_id == celula_id,
                    EjecucionAuditoria.usuario_id == usuario.id,
                    EjecucionAuditoria.fecha_programada == periodo,
                )
            ).first()

        if habilita is not None and dias_rel == 0:
            return _base("disponible", 0, "Disponible hoy",
                         ejecucion.id if ejecucion else None, "iniciar", habilita)
        if habilita is not None:
            return _base(
                "atrasada", dias_rel,
                f"Atrasada hace {dias_rel} día" + ("s" if dias_rel != 1 else ""),
                ejecucion.id if ejecucion else None, "iniciar", habilita,
            )

        # Sin día fijado (proceso/diarias): disponibles todos los días.
        return _base(
            "disponible", 0, "Disponible hoy",
            ejecucion.id if ejecucion else None, "iniciar", None,
        )

    def iniciar_pendiente(
        self, ejecucion_id: int, usuario: Usuario
    ) -> EjecucionAuditoria:
        """Transiciona una ejecución ``pendiente`` a ``en_proceso``."""
        ejecucion = self._repo.obtener_por_id(ejecucion_id)
        if ejecucion is None:
            raise ValueError("Ejecucion de auditoria no encontrada.")
        if ejecucion.estado == "en_proceso":
            # Doble clic o reintento: ya iniciada, se responde la misma.
            self._validar_puede_modificar(ejecucion, usuario)
            return self._enriquecer_read(ejecucion)
        if ejecucion.estado != "pendiente":
            raise ValueError("La ejecución no está en estado pendiente.")

        self._validar_puede_modificar(ejecucion, usuario)

        auditoria = self._session.get(Auditoria, ejecucion.auditoria_id)
        if auditoria is not None:
            self._validar_habilitacion(auditoria)
            self._validar_sin_abierta(
                auditoria,
                usuario,
                ejecucion.celula_id,
                periodo=ejecucion.fecha_programada,
                excluir_ejecucion_id=ejecucion.id,
            )

        ejecucion.estado = "en_proceso"
        ejecucion.fecha = datetime.now(timezone.utc)
        self._repo.actualizar(ejecucion)

        self._session.expire(ejecucion)
        ejecucion = self._repo.obtener_por_id(ejecucion_id)
        if ejecucion is None:
            raise ValueError("Ejecucion de auditoria no encontrada.")
        return self._enriquecer_read(ejecucion)

    def guardar_respuestas(
        self,
        ejecucion_id: int,
        respuestas: list[dict],
        usuario: Usuario,
    ) -> EjecucionAuditoria:
        ejecucion = self._repo.obtener_por_id(ejecucion_id)
        if ejecucion is None:
            raise ValueError("Ejecucion de auditoria no encontrada.")
        if ejecucion.estado == "no_elaborada":
            raise ValueError(
                "Esta auditoría fue marcada como no elaborada y ya no puede "
                "responderse fuera del día en que debía realizarse."
            )
        if ejecucion.estado == "finalizada":
            raise ValueError(
                "No se puede modificar una ejecucion ya finalizada."
            )
        if ejecucion.estado == "pendiente":
            raise ValueError(
                "Debe iniciar la ejecución programada antes de responder."
            )

        self._validar_puede_modificar(ejecucion, usuario)

        auditoria = self._session.get(Auditoria, ejecucion.auditoria_id)

        for item in respuestas:
            criterio_id = item.get("criterio_id")
            valor = item.get("valor")
            observaciones = item.get("observaciones")

            if criterio_id is None or valor is None:
                raise ValueError(
                    "criterio_id y valor son requeridos para cada respuesta."
                )

            valores_permitidos = self._valores_permitidos_por_auditoria(auditoria)

            if valor not in valores_permitidos:
                raise ValueError(
                    f"Valor de respuesta invalido '{valor}'. "
                    f"Debe ser uno de: {', '.join(sorted(valores_permitidos))}."
                )

            criterio = self._session.get(Criterio, criterio_id)
            if criterio is None:
                raise ValueError(
                    f"Criterio {criterio_id} no encontrado."
                )
            if criterio.auditoria_id != ejecucion.auditoria_id:
                raise ValueError(
                    f"El criterio {criterio_id} no pertenece a esta auditoria."
                )

            existente = self._respuesta_repo.obtener_por_ejecucion_y_criterio(
                ejecucion_id, criterio_id
            )

            if existente:
                existente.valor = valor
                existente.observaciones = observaciones
                self._respuesta_repo.actualizar(existente)
            else:
                respuesta = Respuesta(
                    valor=valor,
                    observaciones=observaciones,
                    ejecucion_auditoria_id=ejecucion_id,
                    criterio_id=criterio_id,
                )
                self._respuesta_repo.crear(respuesta)

        self._session.expire(ejecucion)
        ejecucion = self._repo.obtener_por_id(ejecucion_id)
        if ejecucion is None:
            raise ValueError("Ejecucion de auditoria no encontrada.")
        return self._enriquecer_read(ejecucion)

    def finalizar(self, ejecucion_id: int, usuario: Usuario) -> EjecucionAuditoria:
        ejecucion = self._repo.obtener_por_id(ejecucion_id)
        if ejecucion is None:
            raise ValueError("Ejecucion de auditoria no encontrada.")
        if ejecucion.estado == "finalizada":
            raise ValueError("La ejecucion ya esta finalizada.")
        if ejecucion.estado == "no_elaborada":
            raise ValueError(
                "Esta auditoría fue marcada como no elaborada y no puede "
                "finalizarse fuera del día en que debía realizarse."
            )

        self._validar_puede_modificar(ejecucion, usuario)

        criterios_activos = list(
            self._session.exec(
                select(Criterio).where(
                    Criterio.auditoria_id == ejecucion.auditoria_id,
                    Criterio.activo == True,
                )
            ).all()
        )

        respuestas = self._respuesta_repo.listar_por_ejecucion(ejecucion_id)

        criterios_ids = {c.id for c in criterios_activos}
        respondidos_ids = {r.criterio_id for r in respuestas}

        faltantes = criterios_ids - respondidos_ids
        if faltantes:
            raise ValueError(
                f"Faltan respuestas para los criterios: {sorted(faltantes)}"
            )

        ejecucion.estado = "finalizada"
        self._repo.actualizar(ejecucion)
        self._session.expire(ejecucion)
        ejecucion = self._repo.obtener_por_id(ejecucion_id)
        if ejecucion is None:
            raise ValueError("Ejecucion de auditoria no encontrada.")
        return self._enriquecer_read(ejecucion)
