"""Endpoints para la gestion de hallazgos."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.auth.dependencies import get_current_active_user
from app.db.database import get_session
from app.models.usuario import Usuario
from app.schemas.hallazgo import HallazgoBase, HallazgoCreate, HallazgoDetallado, HallazgoUpdate
from app.services.hallazgo_service import HallazgoService

router = APIRouter(tags=["hallazgos"])


def _a_http_error(error: ValueError) -> HTTPException:
    mensaje = str(error).lower()
    if "no encontrad" in mensaje:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )
    if "ya existe" in mensaje or "ya finalized" in mensaje or "valor" in mensaje:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(error),
    )


@router.post(
    "/respuestas/{respuesta_id}/hallazgo",
    response_model=HallazgoDetallado,
    status_code=status.HTTP_201_CREATED,
)
def crear_hallazgo(
    respuesta_id: int,
    datos: HallazgoBase,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Crea un hallazgo asociado a una respuesta con valor ``A`` o ``R``.

    El ``respuesta_id`` proviene del path; el body solo requiere ``descripcion``.
    """
    payload = HallazgoCreate(
        descripcion=datos.descripcion,
        respuesta_id=respuesta_id,
    )
    service = HallazgoService(session)
    try:
        return service.crear(payload, usuario)
    except ValueError as error:
        raise _a_http_error(error)


@router.get(
    "/hallazgos/{hallazgo_id}",
    response_model=HallazgoDetallado,
)
def obtener_hallazgo(
    hallazgo_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Obtiene un hallazgo con su contexto de ejecucion, auditoria, celula y criterio."""
    service = HallazgoService(session)
    try:
        return service.obtener_por_id(hallazgo_id)
    except ValueError as error:
        raise _a_http_error(error)


@router.put(
    "/hallazgos/{hallazgo_id}",
    response_model=HallazgoDetallado,
)
def actualizar_hallazgo(
    hallazgo_id: int,
    datos: HallazgoUpdate,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Actualiza la descripcion de un hallazgo mientras la ejecucion no este finalizada."""
    service = HallazgoService(session)
    try:
        return service.actualizar(hallazgo_id, datos, usuario)
    except ValueError as error:
        raise _a_http_error(error)


@router.delete(
    "/hallazgos/{hallazgo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def eliminar_hallazgo(
    hallazgo_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Elimina un hallazgo de forma controlada mientras la ejecucion este en proceso."""
    service = HallazgoService(session)
    try:
        service.eliminar(hallazgo_id, usuario)
    except ValueError as error:
        raise _a_http_error(error)
    return None