"""Lógica de negocio para la entidad Usuario."""

from sqlmodel import Session, delete, select

from app.auth.security import hash_password
from app.models.area import Area
from app.models.celula import Celula
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.models.usuario_supervisor import UsuarioSupervisor
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate


class UsuarioService:
    """Servicio que encapsula la lógica de negocio de usuarios."""

    def __init__(self, session: Session) -> None:
        self._repo = UsuarioRepository(session)
        self._session = session

    def _es_rol_administrador(self, rol_id: int) -> bool:
        """Indica si un identificador de rol corresponde a Administrador."""
        rol = self._session.exec(
            select(Rol).where(Rol.id == rol_id)
        ).first()
        return rol is not None and rol.nombre == "Administrador"

    def listar(self, skip: int = 0, limit: int = 100) -> list[Usuario]:
        """Obtiene un listado paginado de usuarios.

        Args:
            skip: Registros a omitir (offset).
            limit: Máximo de registros a devolver.

        Returns:
            Lista de instancias de :class:`Usuario`.
        """
        return self._repo.listar(skip=skip, limit=limit)

    def obtener_por_id(self, usuario_id: int) -> Usuario:
        """Busca un usuario por su identificador.

        Args:
            usuario_id: ID del usuario a consultar.

        Returns:
            Instancia de :class:`Usuario`.

        Raises:
            ValueError: Si el usuario no existe.
        """
        usuario = self._repo.obtener_por_id(usuario_id)
        if usuario is None:
            raise ValueError("Usuario no encontrado.")
        return usuario

    def crear(self, datos: UsuarioCreate) -> Usuario:
        """Crea un usuario aplicando las reglas de negocio.

        Args:
            datos: Esquema con los datos del nuevo usuario.

        Returns:
            Instancia de :class:`Usuario` persistida.

        Raises:
            ValueError: Si el correo ya está registrado.
        """
        if self._repo.obtener_por_correo(datos.correo):
            raise ValueError("Ya existe un usuario con ese correo electrónico.")

        if self._es_rol_administrador(datos.rol_id):
            raise ValueError(
                "No se puede crear otro usuario con rol Administrador."
            )

        usuario = Usuario(
            nombre=datos.nombre,
            correo=datos.correo,
            contrasena_hash=hash_password(datos.contrasena),
            activo=datos.activo,
            rol_id=datos.rol_id,
        )

        return self._repo.crear(usuario)

    def actualizar(self, usuario_id: int, datos: UsuarioUpdate) -> Usuario:
        """Actualiza un usuario aplicando las reglas de negocio.

        Args:
            usuario_id: ID del usuario a modificar.
            datos: Esquema con los campos a actualizar. Solo los campos
                con valor distinto de ``None`` se aplican.

        Returns:
            Instancia de :class:`Usuario` actualizada.

        Raises:
            ValueError: Si el usuario no existe o el correo ya está en uso.
        """
        usuario = self.obtener_por_id(usuario_id)

        if datos.correo is not None and datos.correo != usuario.correo:
            existente = self._repo.obtener_por_correo(datos.correo)
            if existente is not None and existente.id != usuario_id:
                raise ValueError(
                    "Ya existe un usuario con ese correo electrónico."
                )

        if datos.nombre is not None:
            usuario.nombre = datos.nombre
        if datos.correo is not None:
            usuario.correo = datos.correo
        if datos.activo is not None:
            usuario.activo = datos.activo
        if datos.rol_id is not None:
            if (
                datos.rol_id != usuario.rol_id
                and self._es_rol_administrador(datos.rol_id)
            ):
                raise ValueError(
                    "No se puede asignar el rol Administrador a otro usuario."
                )
            usuario.rol_id = datos.rol_id
        if datos.contrasena is not None:
            usuario.contrasena_hash = hash_password(datos.contrasena)

        return self._repo.actualizar(usuario)

    def cambiar_estado(
        self, usuario_id: int, activo: bool, current_user_id: int
    ) -> Usuario:
        """Activa o desactiva un usuario.

        Args:
            usuario_id: ID del usuario cuyo estado se va a cambiar.
            activo: ``True`` para activar, ``False`` para desactivar.
            current_user_id: ID del administrador que realiza la operación.

        Returns:
            Instancia de :class:`Usuario` actualizada.

        Raises:
            ValueError: Si el usuario no existe o el administrador
                intenta desactivarse a sí mismo.
        """
        usuario = self.obtener_por_id(usuario_id)

        if usuario.activo == activo:
            return usuario

        if not activo and usuario_id == current_user_id:
            raise ValueError("No puedes desactivar tu propio usuario.")

        usuario.activo = activo
        return self._repo.actualizar(usuario)

    def obtener_asignacion(self, usuario_id: int) -> dict:
        """Devuelve las áreas, células y supervisores a cargo de un usuario."""
        usuario = self.obtener_por_id(usuario_id)
        supervisor_ids = [
            s.supervisor_id
            for s in self._session.exec(
                select(UsuarioSupervisor).where(
                    UsuarioSupervisor.gerente_id == usuario_id
                )
            ).all()
        ]
        return {
            "area_ids": [a.id for a in usuario.areas],
            "celula_ids": [c.id for c in usuario.celulas],
            "supervisor_ids": supervisor_ids,
        }

    def _rol_nombre(self, usuario: Usuario) -> str:
        rol = self._session.get(Rol, usuario.rol_id)
        return rol.nombre if rol else ""

    def asignar(
        self,
        usuario_id: int,
        area_ids: list[int],
        celula_ids: list[int],
        supervisor_ids: list[int] | None = None,
    ) -> Usuario:
        """Asigna recursos a un usuario según su rol.

        - Auditor: áreas y células a cargo.
        - Supervisor: solo áreas (sin células).
        - Gerente: supervisores a su cargo.
        """
        usuario = self.obtener_por_id(usuario_id)
        rol_nombre = self._rol_nombre(usuario)

        if rol_nombre == "Auditor":
            self._asignar_areas_celulas(usuario, area_ids, celula_ids)
        elif rol_nombre == "Supervisor":
            if celula_ids:
                raise ValueError(
                    "Los supervisores no tienen células a cargo; solo áreas."
                )
            self._asignar_areas_celulas(usuario, area_ids, [])
        elif rol_nombre == "Gerente":
            self._asignar_supervisores(usuario_id, supervisor_ids or [])
        else:  # Administrador u otros: sin asignación.
            self._asignar_areas_celulas(usuario, [], [])
            self._asignar_supervisores(usuario_id, [])

        return usuario

    def _asignar_areas_celulas(
        self,
        usuario: Usuario,
        area_ids: list[int],
        celula_ids: list[int],
    ) -> None:
        areas: list[Area] = []
        area_ids_unicos = set(area_ids)
        for area_id in area_ids_unicos:
            area = self._session.get(Area, area_id)
            if area is None or not area.activa:
                raise ValueError("El área no existe o está inactiva.")
            areas.append(area)

        celulas: list[Celula] = []
        for celula_id in set(celula_ids):
            celula = self._session.get(Celula, celula_id)
            if celula is None or not celula.activa:
                raise ValueError("La célula no existe o está inactiva.")
            if celula.area_id not in area_ids_unicos:
                raise ValueError(
                    "Una célula asignada no pertenece a un área del usuario."
                )
            celulas.append(celula)

        usuario.areas = areas
        usuario.celulas = celulas
        self._repo.actualizar(usuario)

    def _asignar_supervisores(
        self, gerente_id: int, supervisor_ids: list[int]
    ) -> None:
        """Reemplaza los supervisores a cargo de un gerente."""
        self._session.exec(
            delete(UsuarioSupervisor).where(
                UsuarioSupervisor.gerente_id == gerente_id
            )
        )
        for supervisor_id in set(supervisor_ids):
            supervisor = self._session.get(Usuario, supervisor_id)
            if supervisor is None or not supervisor.activo:
                raise ValueError("El supervisor no existe o está inactivo.")
            if self._session.get(Rol, supervisor.rol_id).nombre != "Supervisor":
                raise ValueError("El usuario seleccionado no es Supervisor.")
            self._session.add(
                UsuarioSupervisor(
                    gerente_id=gerente_id, supervisor_id=supervisor_id
                )
            )
        self._session.commit()
