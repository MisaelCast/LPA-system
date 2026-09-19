"""Lógica de negocio para la entidad Usuario."""

from sqlmodel import Session, select

from app.auth.security import hash_password
from app.models.rol import Rol
from app.models.usuario import Usuario
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
