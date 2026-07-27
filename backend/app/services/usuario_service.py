"""Lógica de negocio para la entidad Usuario."""

from sqlmodel import Session

from app.auth.security import hash_password
from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate


class UsuarioService:
    """Servicio que encapsula la lógica de negocio de usuarios."""

    def __init__(self, session: Session) -> None:
        self._repo = UsuarioRepository(session)

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
            usuario.rol_id = datos.rol_id
        if datos.contrasena is not None:
            usuario.contrasena_hash = hash_password(datos.contrasena)

        return self._repo.actualizar(usuario)
