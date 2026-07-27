"""Lógica de negocio para la entidad Usuario."""

from sqlmodel import Session

from app.auth.security import hash_password
from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario import UsuarioCreate


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
