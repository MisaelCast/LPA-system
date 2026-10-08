"""Endpoints para la gestión de usuarios."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.auth.permissions import require_roles
from app.db.database import get_session
from app.models.usuario import Usuario
from app.schemas.usuario import (
    AsignacionRead,
    AsignacionUpdate,
    UsuarioCreate,
    UsuarioEstadoUpdate,
    UsuarioRead,
    UsuarioUpdate,
)
from app.services.usuario_service import UsuarioService

router = APIRouter(tags=["usuarios"])


@router.get("/usuarios", response_model=list[UsuarioRead])
def listar_usuarios(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> list[Usuario]:
    """Lista los usuarios del sistema con paginación.

    Solo accesible por usuarios con rol **Administrador**.
    """
    return UsuarioService(session).listar(skip=skip, limit=limit)


@router.get("/usuarios/asignacion-opciones")
def opciones_asignacion(
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> dict:
    """Devuelve áreas, células y supervisores para el formulario de asignación."""
    from sqlmodel import select

    from app.models.rol import Rol
    from app.models.usuario import Usuario as UsuarioModel
    from app.services.area_service import AreaService
    from app.services.celula_service import CelulaService

    areas = AreaService(session).listar_activas()
    celulas = CelulaService(session).listar_todas()
    supervisores = list(
        session.exec(
            select(UsuarioModel)
            .join(Rol, UsuarioModel.rol_id == Rol.id)
            .where(Rol.nombre == "Supervisor", UsuarioModel.activo == True)  # noqa: E712
            .order_by(UsuarioModel.nombre)
        ).all()
    )
    return {
        "areas": areas,
        "celulas": celulas,
        "supervisores": supervisores,
    }


@router.get("/usuarios/{usuario_id}", response_model=UsuarioRead)
def obtener_usuario(
    usuario_id: int,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Usuario:
    """Consulta un usuario por su identificador.

    Solo accesible por usuarios con rol **Administrador**.
    """
    service = UsuarioService(session)
    try:
        return service.obtener_por_id(usuario_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@router.get("/usuarios/{usuario_id}/asignacion", response_model=AsignacionRead)
def obtener_asignacion_usuario(
    usuario_id: int,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> dict:
    """Devuelve las áreas y células asignadas a un usuario."""
    service = UsuarioService(session)
    try:
        return service.obtener_asignacion(usuario_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@router.put("/usuarios/{usuario_id}/asignacion", response_model=AsignacionRead)
def asignar_usuario(
    usuario_id: int,
    datos: AsignacionUpdate,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> dict:
    """Asigna áreas, células y/o supervisores a cargo de un usuario según su rol."""
    service = UsuarioService(session)
    try:
        service.asignar(
            usuario_id,
            datos.area_ids,
            datos.celula_ids,
            datos.supervisor_ids,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )
    return service.obtener_asignacion(usuario_id)


@router.patch("/usuarios/{usuario_id}/estado", response_model=UsuarioRead)
def cambiar_estado_usuario(
    usuario_id: int,
    datos: UsuarioEstadoUpdate,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(require_roles("Administrador")),
) -> Usuario:
    """Activa o desactiva un usuario del sistema.

    Un administrador no puede desactivarse a sí mismo.
    Solo accesible por usuarios con rol **Administrador**.
    """
    service = UsuarioService(session)
    try:
        return service.cambiar_estado(usuario_id, datos.activo, current_user.id)
    except ValueError as error:
        if "no encontrado" in str(error).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        )


@router.put("/usuarios/{usuario_id}", response_model=UsuarioRead)
def actualizar_usuario(
    usuario_id: int,
    datos: UsuarioUpdate,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Usuario:
    """Actualiza los datos de un usuario existente.

    Solo los campos enviados en el cuerpo serán modificados.
    Solo accesible por usuarios con rol **Administrador**.
    """
    service = UsuarioService(session)
    try:
        return service.actualizar(usuario_id, datos)
    except ValueError as error:
        if "no encontrado" in str(error).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )


@router.post(
    "/usuarios",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_usuario(
    datos: UsuarioCreate,
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> Usuario:
    """Crea un nuevo usuario en el sistema.

    Solo accesible por usuarios con rol **Administrador**.
    """
    service = UsuarioService(session)
    try:
        return service.crear(datos)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )
