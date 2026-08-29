"""Logica de negocio para EjecucionAuditoria y Respuesta."""

from datetime import datetime

from sqlmodel import Session, func, select

from app.models.area import Area
from app.models.auditoria import Auditoria
from app.models.celula import Celula
from app.models.criterio import Criterio
from app.models.ejecucion_auditoria import EjecucionAuditoria
from app.models.hallazgo import Hallazgo
from app.models.respuesta import Respuesta
from app.models.usuario import Usuario
from app.repositories.ejecucion_auditoria_repository import (
    EjecucionAuditoriaRepository,
)
from app.repositories.respuesta_repository import RespuestaRepository


class EjecucionAuditoriaService:
    """Servicio que encapsula la logica de negocio de ejecuciones de auditoria."""

    def __init__(self, session: Session) -> None:
        self._repo = EjecucionAuditoriaRepository(session)
        self._respuesta_repo = RespuestaRepository(session)
        self._session = session

    def _enriquecer_read(
        self, ejecucion: EjecucionAuditoria
    ) -> EjecucionAuditoria:
        object.__setattr__(ejecucion, "auditoria_nombre", "")
        object.__setattr__(ejecucion, "area_nombre", "")
        object.__setattr__(ejecucion, "celula_numero", None)
        object.__setattr__(ejecucion, "auditor_nombre", "")

        auditoria = self._session.get(Auditoria, ejecucion.auditoria_id)
        if auditoria:
            object.__setattr__(ejecucion, "auditoria_nombre", auditoria.nombre)
            if auditoria.area_id:
                from app.models.area import Area

                area = self._session.get(Area, auditoria.area_id)
                if area:
                    object.__setattr__(ejecucion, "area_nombre", area.nombre)

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
        auditorias = list(
            self._session.exec(
                select(Auditoria).where(Auditoria.activa == True)
            ).all()
        )
        return [self._enriquecer_auditoria(a) for a in auditorias]

    def _enriquecer_auditoria(self, auditoria: Auditoria) -> Auditoria:
        object.__setattr__(auditoria, "capa_nombre", "")
        object.__setattr__(auditoria, "frecuencia_nombre", "")
        object.__setattr__(auditoria, "area_nombre", None)

        if auditoria.capa_id is not None:
            from app.models.capa import Capa
            capa = self._session.get(Capa, auditoria.capa_id)
            if capa:
                object.__setattr__(auditoria, "capa_nombre", capa.nombre)

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

    def obtener_celulas_disponibles(self, auditoria_id: int) -> list[Celula]:
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

        return list(
            self._session.exec(
                select(Celula).where(
                    Celula.area_id == auditoria.area_id,
                    Celula.activa == True,
                )
            ).all()
        )

    def iniciar(
        self, auditoria_id: int, usuario: Usuario, celula_id: int | None = None
    ) -> EjecucionAuditoria:
        auditoria = self._session.get(Auditoria, auditoria_id)
        if auditoria is None:
            raise ValueError("Auditoria no encontrada.")
        if not auditoria.activa:
            raise ValueError("La auditoria no esta activa.")

        if celula_id is not None:
            celula = self._session.get(Celula, celula_id)
            if celula is None:
                raise ValueError("Celula no encontrada.")
            if not celula.activa:
                raise ValueError("La celula no esta activa.")
            if auditoria.area_id is not None and celula.area_id != auditoria.area_id:
                raise ValueError(
                    "La celula no pertenece al area de la auditoria."
                )

        ejecucion = EjecucionAuditoria(
            fecha=datetime.utcnow(),
            estado="en_proceso",
            auditoria_id=auditoria.id,
            usuario_id=usuario.id,
            celula_id=celula_id,
        )
        return self._repo.crear(ejecucion)

    def obtener_por_id(self, ejecucion_id: int) -> EjecucionAuditoria:
        ejecucion = self._repo.obtener_por_id(ejecucion_id)
        if ejecucion is None:
            raise ValueError("Ejecucion de auditoria no encontrada.")
        return self._enriquecer_read(ejecucion)

    def _es_admin(self, usuario: Usuario) -> bool:
        rol = getattr(usuario, "rol", None)
        return getattr(rol, "nombre", "") == "Administrador"

    def _resumen_de_respuestas(
        self, respuestas: list[Respuesta], total_criterios: int
    ) -> dict:
        total_v = sum(1 for r in respuestas if r.valor == "V")
        total_a = sum(1 for r in respuestas if r.valor == "A")
        total_r = sum(1 for r in respuestas if r.valor == "R")
        return {
            "total_criterios": total_criterios,
            "total_v": total_v,
            "total_a": total_a,
            "total_r": total_r,
        }

    def _contar_criterios_activos(self, auditoria_id: int) -> int:
        return self._session.exec(
            select(func.count()).select_from(Criterio).where(
                Criterio.auditoria_id == auditoria_id,
                Criterio.activo == True,  # noqa: E712
            )
        ).one()

    def _a_list_item(
        self, ejecucion: EjecucionAuditoria, respuestas: list[Respuesta]
    ) -> dict:
        auditoria_nombre = ""
        area_id: int | None = None
        area_nombre: str | None = None

        auditoria = self._session.get(Auditoria, ejecucion.auditoria_id)
        if auditoria:
            auditoria_nombre = auditoria.nombre
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
    ) -> list[dict]:
        """Lista las ejecuciones del historial con sus resumenes V/A/R.

        Un auditor solo ve sus propias ejecuciones; un administrador ve todas.
        """
        if not self._es_admin(usuario):
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

    def obtener_detalle(self, ejecucion_id: int) -> dict:
        """Devuelve el detalle completo de una ejecucion con resumen V/A/R."""
        ejecucion = self.obtener_por_id(ejecucion_id)

        respuestas = self._respuesta_repo.listar_por_ejecucion(ejecucion_id)
        total_criterios = self._contar_criterios_activos(ejecucion.auditoria_id)

        area_id: int | None = None
        auditoria = self._session.get(Auditoria, ejecucion.auditoria_id)
        if auditoria and auditoria.area_id:
            area_id = auditoria.area_id

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
            "criterios": getattr(ejecucion, "criterios", []),
            "resumen": self._resumen_de_respuestas(respuestas, total_criterios),
        }

    def guardar_respuestas(
        self,
        ejecucion_id: int,
        respuestas: list[dict],
        usuario: Usuario,
    ) -> EjecucionAuditoria:
        ejecucion = self._repo.obtener_por_id(ejecucion_id)
        if ejecucion is None:
            raise ValueError("Ejecucion de auditoria no encontrada.")
        if ejecucion.estado == "finalizada":
            raise ValueError(
                "No se puede modificar una ejecucion ya finalizada."
            )

        auditoria = self._session.get(Auditoria, ejecucion.auditoria_id)

        for item in respuestas:
            criterio_id = item.get("criterio_id")
            valor = item.get("valor")
            observaciones = item.get("observaciones")

            if criterio_id is None or valor is None:
                raise ValueError(
                    "criterio_id y valor son requeridos para cada respuesta."
                )

            if valor not in ("V", "A", "R"):
                raise ValueError(
                    f"Valor de respuesta invalido '{valor}'. "
                    "Debe ser V, A o R."
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
