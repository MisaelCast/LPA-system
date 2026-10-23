"""Logica de negocio para la entidad Auditoria."""

from sqlmodel import Session, func, select

from app.models.area import Area
from app.models.auditoria import Auditoria
from app.models.auditoria_dia import AuditoriaDia, dias_elegidos
from app.repositories.auditoria_repository import AuditoriaRepository
from app.schemas.auditoria import AuditoriaCreate, AuditoriaUpdate
from app.services.capa_service import CapaService
from app.services.frecuencia_service import FrecuenciaService

# Jerarquia de capas: un rol puede gestionar las auditorias de su capa y las
# inferiores (p. ej. un Supervisor gestiona auditorias de capa Supervisor y
# Auditor).
JERARQUIA_CAPAS: tuple[str, ...] = ("Auditor", "Supervisor", "Gerente")

# Roles que pueden gestionar (crear/editar/eliminar) auditorias.
ROLES_GESTION_AUDITORIAS: tuple[str, ...] = (
    "Administrador",
    "Supervisor",
    "Gerente",
)


def _rol_nombre(usuario) -> str:
    return getattr(getattr(usuario, "rol", None), "nombre", "")


def _capas_ids_permitidas(session: Session, usuario) -> list[int] | None:
    """Capas que el usuario puede gestionar. ``None`` = todas."""
    rol = _rol_nombre(usuario)
    if rol == "Administrador":
        return None
    if rol not in JERARQUIA_CAPAS:
        return []
    desde = JERARQUIA_CAPAS.index(rol)
    nombres = set(JERARQUIA_CAPAS[: desde + 1])
    from app.models.capa import Capa

    return sorted(
        capa.id
        for capa in session.exec(select(Capa).where(Capa.activa == True)).all()  # noqa: E712
        if capa.nombre in nombres and capa.id is not None
    )


def _areas_ids_permitidas(session: Session, usuario) -> list[int] | None:
    """Áreas donde el usuario puede gestionar auditorías.

    ``None`` = cualquier área (Administrador y Gerente). Un Supervisor solo
    puede gestionar auditorías de sus áreas asignadas.
    """
    rol = _rol_nombre(usuario)
    if rol in ("Administrador", "Gerente"):
        return None
    if rol != "Supervisor":
        return []
    areas_ids = {a.id for a in usuario.areas if a.id is not None}
    return sorted(areas_ids)


def permisos_gestion(session: Session, usuario) -> dict:
    """Permisos de gestión de auditorías para el usuario autenticado.

    Además de los IDs permitidos (``None`` = sin restricción), incluye las
    opciones de capa, área y frecuencia ya filtradas para que el frontend
    no necesite consultar catálogos restringidos a Administrador.
    """
    from app.models.capa import Capa
    from app.models.frecuencia import Frecuencia

    rol = _rol_nombre(usuario)
    capas_ids = _capas_ids_permitidas(session, usuario)
    areas_ids = _areas_ids_permitidas(session, usuario)

    capas = session.exec(select(Capa).where(Capa.activa == True)).all()  # noqa: E712
    if capas_ids is not None:
        capas = [c for c in capas if c.id in capas_ids]

    areas = session.exec(select(Area).where(Area.activa == True)).all()  # noqa: E712
    if areas_ids is not None:
        areas = [a for a in areas if a.id in areas_ids]

    frecuencias = session.exec(select(Frecuencia)).all()

    return {
        "puede_gestionar": rol in ROLES_GESTION_AUDITORIAS,
        "capa_ids": capas_ids,
        "area_ids": areas_ids,
        "capas": [{"id": c.id, "nombre": c.nombre} for c in capas],
        "areas": [{"id": a.id, "nombre": a.nombre} for a in areas],
        "frecuencias": [
            {"id": f.id, "nombre": f.nombre} for f in frecuencias
        ],
    }


def _validar_capa_area(
    session: Session, usuario, capa_id: int, area_id: int | None
) -> None:
    """Valida que el usuario pueda usar esa capa/área en una auditoría."""
    rol = _rol_nombre(usuario)
    if rol not in ROLES_GESTION_AUDITORIAS:
        raise ValueError(
            "No tiene permisos para gestionar auditorías."
        )

    capas_ids = _capas_ids_permitidas(session, usuario)
    if capas_ids is not None and capa_id not in capas_ids:
        raise ValueError(
            "No tiene permisos para crear auditorías de esa capa."
        )

    areas_ids = _areas_ids_permitidas(session, usuario)
    if areas_ids is not None:
        if area_id is None:
            raise ValueError(
                "Debe seleccionar un área de su cargo para la auditoría."
            )
        if area_id not in areas_ids:
            raise ValueError(
                "No tiene permisos para crear auditorías fuera de sus áreas."
            )
        if session.get(Area, area_id) is None:
            raise ValueError("El área especificada no existe.")


def _puede_gestionar_auditoria(
    session: Session, usuario, auditoria: Auditoria
) -> bool:
    """Indica si el usuario puede modificar la auditoría indicada."""
    rol = _rol_nombre(usuario)
    if rol == "Administrador":
        return True
    if rol not in ROLES_GESTION_AUDITORIAS:
        return False

    capas_ids = _capas_ids_permitidas(session, usuario)
    if capas_ids is not None and auditoria.capa_id not in capas_ids:
        return False

    areas_ids = _areas_ids_permitidas(session, usuario)
    if areas_ids is not None:
        return (
            auditoria.area_id is not None and auditoria.area_id in areas_ids
        )
    return True


class AuditoriaService:
    """Servicio que encapsula la logica de negocio de auditorias."""

    def __init__(self, session: Session) -> None:
        self._repo = AuditoriaRepository(session)
        self._session = session

    def _enriquecer_read(self, auditoria: Auditoria) -> Auditoria:
        """Adjunta nombres de entidades relacionadas para serializacion."""
        object.__setattr__(auditoria, "capa_nombre", "")
        object.__setattr__(auditoria, "frecuencia_nombre", "")
        object.__setattr__(auditoria, "area_nombre", None)
        object.__setattr__(auditoria, "dias_semana", dias_elegidos(auditoria))

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
            area = self._session.get(Area, auditoria.area_id)
            if area:
                object.__setattr__(auditoria, "area_nombre", area.nombre)

        return auditoria

    def listar(
        self, usuario, skip: int = 0, limit: int = 100
    ) -> list[Auditoria]:
        """Listado paginado de auditorías visibles para el usuario.

        Un Supervisor solo ve las auditorías de sus capas y áreas; un Gerente
        ve las de su capa y las inferiores (en cualquier área).
        """
        auditorias = self._repo.listar(skip=skip, limit=limit)

        capas_ids = _capas_ids_permitidas(self._session, usuario)
        areas_ids = _areas_ids_permitidas(self._session, usuario)
        if capas_ids is not None:
            auditorias = [a for a in auditorias if a.capa_id in capas_ids]
        if areas_ids is not None:
            auditorias = [
                a for a in auditorias if a.area_id in areas_ids
            ]

        return [self._enriquecer_read(a) for a in auditorias]

    def permisos(self, usuario) -> dict:
        """Permisos de gestión para mostrar en el formulario del frontend."""
        return permisos_gestion(self._session, usuario)

    def puede_gestionar(self, usuario, auditoria: Auditoria) -> bool:
        """Expone la validación de gestión (usada también por criterios)."""
        return _puede_gestionar_auditoria(self._session, usuario, auditoria)

    def obtener_por_id(self, auditoria_id: int) -> Auditoria:
        """Busca una auditoria por su identificador.

        Raises:
            ValueError: Si la auditoria no existe.
        """
        auditoria = self._repo.obtener_por_id(auditoria_id)
        if auditoria is None:
            raise ValueError("Auditoria no encontrada.")
        return self._enriquecer_read(auditoria)

    def crear(self, datos: AuditoriaCreate, usuario) -> Auditoria:
        """Crea una auditoria aplicando las reglas de negocio.

        Además de las validaciones de FK, aplica las restricciones del rol:
        capa propia o inferior y, para Supervisores, solo sus áreas.

        Raises:
            ValueError: Si el nombre ya esta registrado, una FK no existe o
                        el usuario no tiene permisos.
        """
        if self._repo.obtener_por_nombre(datos.nombre):
            raise ValueError("Ya existe una auditoria con ese nombre.")

        capa_service = CapaService(self._session)
        try:
            capa_service.obtener_por_id(datos.capa_id)
        except ValueError:
            raise ValueError("La capa especificada no existe.")

        frecuencia_service = FrecuenciaService(self._session)
        try:
            frecuencia_service.obtener_por_id(datos.frecuencia_id)
        except ValueError:
            raise ValueError("La frecuencia especificada no existe.")

        _validar_capa_area(self._session, usuario, datos.capa_id, datos.area_id)

        auditoria = Auditoria(
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            activa=datos.activa,
            capa_id=datos.capa_id,
            frecuencia_id=datos.frecuencia_id,
            area_id=datos.area_id,
        )

        creada = self._repo.crear(auditoria)

        dias = list(datos.dias_semana or [])
        if dias and creada.id is not None:
            for dia in dias:
                self._session.add(
                    AuditoriaDia(auditoria_id=creada.id, dia_semana=dia)
                )
            self._session.commit()
        object.__setattr__(creada, "dias_semana", dias)

        return self._enriquecer_read(creada)

    def _reemplazar_dias(self, auditoria_id: int, dias: list[int]) -> None:
        """Reemplaza los días elegidos de una auditoría por ``dias``."""
        existentes = list(
            self._session.exec(
                select(AuditoriaDia).where(
                    AuditoriaDia.auditoria_id == auditoria_id
                )
            ).all()
        )
        nuevos = set(dias)
        for fila in existentes:
            if fila.dia_semana not in nuevos:
                self._session.delete(fila)
        presentes = {f.dia_semana for f in existentes}
        for dia in sorted(nuevos - presentes):
            self._session.add(
                AuditoriaDia(auditoria_id=auditoria_id, dia_semana=dia)
            )
        self._session.commit()

    def actualizar(
        self, auditoria_id: int, datos: AuditoriaUpdate, usuario
    ) -> Auditoria:
        """Actualiza una auditoria aplicando las reglas de negocio.

        Solo el Administrador puede editar auditorías ajenas; un Supervisor o
        Gerente solo las de sus capas/áreas.

        Raises:
            ValueError: Si la auditoria no existe,
                        el nombre ya esta en uso,
                        una FK no existe o el usuario no tiene permisos.
        """
        auditoria = self._repo.obtener_por_id(auditoria_id)
        if auditoria is None:
            raise ValueError("Auditoria no encontrada.")

        if not _puede_gestionar_auditoria(self._session, usuario, auditoria):
            raise ValueError(
                "No tiene permisos para modificar esta auditoría."
            )

        if datos.nombre is not None and datos.nombre != auditoria.nombre:
            existente = self._repo.obtener_por_nombre(datos.nombre)
            if existente is not None and existente.id != auditoria_id:
                raise ValueError("Ya existe una auditoria con ese nombre.")

        if datos.capa_id is not None:
            from app.models.capa import Capa

            if self._session.get(Capa, datos.capa_id) is None:
                raise ValueError("La capa especificada no existe.")

        if datos.frecuencia_id is not None:
            from app.models.frecuencia import Frecuencia

            if self._session.get(Frecuencia, datos.frecuencia_id) is None:
                raise ValueError("La frecuencia especificada no existe.")

        if datos.capa_id is not None or datos.area_id is not None:
            _validar_capa_area(
                self._session,
                usuario,
                datos.capa_id if datos.capa_id is not None else auditoria.capa_id,
                datos.area_id if datos.area_id is not None else auditoria.area_id,
            )

        if datos.nombre is not None:
            auditoria.nombre = datos.nombre
        if datos.descripcion is not None:
            auditoria.descripcion = datos.descripcion
        if datos.activa is not None:
            auditoria.activa = datos.activa
        if datos.capa_id is not None:
            auditoria.capa_id = datos.capa_id
        if datos.frecuencia_id is not None:
            auditoria.frecuencia_id = datos.frecuencia_id
        if datos.area_id is not None:
            auditoria.area_id = datos.area_id

        actualizada = self._repo.actualizar(auditoria)

        if datos.dias_semana is not None and actualizada.id is not None:
            self._reemplazar_dias(actualizada.id, datos.dias_semana)
            object.__setattr__(
                actualizada, "dias_semana", list(datos.dias_semana)
            )

        return self._enriquecer_read(actualizada)

    def cambiar_estado(
        self, auditoria_id: int, activa: bool, usuario
    ) -> Auditoria:
        """Activa o desactiva una auditoria.

        Raises:
            ValueError: Si la auditoria no existe o el usuario no tiene
                        permisos.
        """
        auditoria = self._repo.obtener_por_id(auditoria_id)
        if auditoria is None:
            raise ValueError("Auditoria no encontrada.")

        if not _puede_gestionar_auditoria(self._session, usuario, auditoria):
            raise ValueError(
                "No tiene permisos para modificar esta auditoría."
            )

        if auditoria.activa == activa:
            return self._enriquecer_read(auditoria)

        auditoria.activa = activa
        actualizada = self._repo.actualizar(auditoria)
        return self._enriquecer_read(actualizada)

    def eliminar(self, auditoria_id: int, usuario) -> None:
        """Elimina fisicamente una auditoria si no tiene ejecuciones realizadas.

        Si la auditoria no tiene ejecuciones, tambien se eliminan sus criterios
        asociados (no existen respuestas que los referencien).

        Raises:
            ValueError: Si la auditoria no existe, tiene ejecuciones asociadas
                        o el usuario no tiene permisos.
        """
        from app.models.criterio import Criterio
        from app.models.ejecucion_auditoria import EjecucionAuditoria

        auditoria = self._repo.obtener_por_id(auditoria_id)
        if auditoria is None:
            raise ValueError("Auditoria no encontrada.")

        if not _puede_gestionar_auditoria(self._session, usuario, auditoria):
            raise ValueError(
                "No tiene permisos para eliminar esta auditoría."
            )

        total_ejecuciones = self._session.exec(
            select(func.count())
            .select_from(EjecucionAuditoria)
            .where(EjecucionAuditoria.auditoria_id == auditoria_id)
        ).one()
        if total_ejecuciones > 0:
            raise ValueError(
                "No se puede eliminar la auditoría porque tiene ejecuciones "
                "realizadas asociadas."
            )

        criterios = self._session.exec(
            select(Criterio).where(Criterio.auditoria_id == auditoria_id)
        ).all()
        for criterio in criterios:
            self._session.delete(criterio)

        self._repo.eliminar(auditoria)
