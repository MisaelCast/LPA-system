"""Endpoints para la gestion de auditorias."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.auth.permissions import require_roles
from app.db.database import get_session
from app.models.auditoria import Auditoria
from app.models.usuario import Usuario
from app.schemas.auditoria import (
    AuditoriaCreate,
    AuditoriaEstadoUpdate,
    AuditoriaRead,
    AuditoriaUpdate,
)
from app.services.auditoria_service import (
    ROLES_GESTION_AUDITORIAS,
    AuditoriaService,
)

router = APIRouter(tags=["auditorias"])


def _mapear_error_auditoria(error: ValueError) -> HTTPException:
    """Traduce los ValueErrors del servicio a respuestas HTTP."""
    mensaje = str(error)
    if "no tiene permisos" in mensaje.lower():
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=mensaje,
        )
    if "no encontrada" in mensaje.lower():
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=mensaje,
        )
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=mensaje,
    )


@router.get("/auditorias", response_model=list[AuditoriaRead])
def listar_auditorias(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(
        require_roles(*ROLES_GESTION_AUDITORIAS)
    ),
) -> list[Auditoria]:
    """Lista las auditorías visibles para el rol del usuario.

    Un Supervisor solo ve las de sus capas y áreas; un Gerente ve las de su
    capa y las inferiores.
    """
    return AuditoriaService(session).listar(usuario, skip=skip, limit=limit)


@router.get("/auditorias/permisos-gestion")
def permisos_gestion_auditorias(
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(
        require_roles(*ROLES_GESTION_AUDITORIAS)
    ),
) -> dict:
    """Devuelve las capas y áreas que el usuario puede usar en el formulario.

    ``capa_ids``/``area_ids`` en ``null`` significan «sin restricción».
    """
    return AuditoriaService(session).permisos(usuario)


@router.get("/auditorias/{auditoria_id}", response_model=AuditoriaRead)
def obtener_auditoria(
    auditoria_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(
        require_roles(*ROLES_GESTION_AUDITORIAS)
    ),
) -> Auditoria:
    """Consulta una auditoria por su identificador.

    Un Supervisor o Gerente solo puede consultar las de sus capas/áreas.
    """
    service = AuditoriaService(session)
    try:
        auditoria = service.obtener_por_id(auditoria_id)
        if not service.puede_gestionar(usuario, auditoria):
            raise ValueError("No tiene permisos para ver esta auditoría.")
        return auditoria
    except ValueError as error:
        raise _mapear_error_auditoria(error)


@router.patch("/auditorias/{auditoria_id}/estado", response_model=AuditoriaRead)
def cambiar_estado_auditoria(
    auditoria_id: int,
    datos: AuditoriaEstadoUpdate,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(
        require_roles(*ROLES_GESTION_AUDITORIAS)
    ),
) -> Auditoria:
    """Activa o desactiva una auditoria del sistema.

    Un Supervisor o Gerente solo puede modificar las de sus capas/áreas.
    """
    service = AuditoriaService(session)
    try:
        return service.cambiar_estado(auditoria_id, datos.activa, usuario)
    except ValueError as error:
        raise _mapear_error_auditoria(error)


@router.delete("/auditorias/{auditoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_auditoria(
    auditoria_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(
        require_roles(*ROLES_GESTION_AUDITORIAS)
    ),
) -> None:
    """Elimina fisicamente una auditoria del sistema.

    Un Supervisor o Gerente solo puede eliminar las de sus capas/áreas.
    """
    service = AuditoriaService(session)
    try:
        service.eliminar(auditoria_id, usuario)
    except ValueError as error:
        raise _mapear_error_auditoria(error)


@router.put("/auditorias/{auditoria_id}", response_model=AuditoriaRead)
def actualizar_auditoria(
    auditoria_id: int,
    datos: AuditoriaUpdate,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(
        require_roles(*ROLES_GESTION_AUDITORIAS)
    ),
) -> Auditoria:
    """Actualiza los datos de una auditoria existente.

    Solo los campos enviados en el cuerpo seran modificados.
    Un Supervisor o Gerente solo puede modificar las de sus capas/áreas.
    """
    service = AuditoriaService(session)
    try:
        return service.actualizar(auditoria_id, datos, usuario)
    except ValueError as error:
        raise _mapear_error_auditoria(error)


@router.post(
    "/auditorias",
    response_model=AuditoriaRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_auditoria(
    datos: AuditoriaCreate,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(
        require_roles(*ROLES_GESTION_AUDITORIAS)
    ),
) -> Auditoria:
    """Crea una nueva auditoria en el sistema.

    Un Supervisor solo puede crear auditorías de su capa y la inferior
    (Auditor) en sus áreas asignadas; un Gerente, de su capa y las
    inferiores en cualquier área.
    """
    service = AuditoriaService(session)
    try:
        return service.crear(datos, usuario)
    except ValueError as error:
        raise _mapear_error_auditoria(error)
