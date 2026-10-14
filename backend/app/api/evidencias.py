"""Endpoints para evidencias (fotos) de hallazgos en Supabase Storage."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel import Session

from app.api.hallazgos import _a_http_error
from app.auth.dependencies import get_current_active_user
from app.db.database import get_session
from app.models.usuario import Usuario
from app.schemas.evidencia import EvidenciaOut
from app.services.evidencia_service import EvidenciaService

router = APIRouter(tags=["evidencias"])


@router.post(
    "/hallazgos/{hallazgo_id}/evidencias",
    response_model=EvidenciaOut,
    status_code=status.HTTP_201_CREATED,
)
def subir_evidencia(
    hallazgo_id: int,
    archivo: UploadFile = File(...),
    tipo: str = Form(default="original"),
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Sube una imagen (JPG/PNG/WEBP, max. 5 MB) como evidencia del hallazgo.

    ``tipo`` puede ser ``original`` (hallazgo) o ``correccion`` (del responsable).
    """
    contenido = archivo.file.read()
    try:
        return EvidenciaService(session).subir(
            hallazgo_id, archivo.filename, contenido, usuario, tipo
        )
    except ValueError as error:
        raise _a_http_error(error) from error


@router.get(
    "/hallazgos/{hallazgo_id}/evidencias",
    response_model=list[EvidenciaOut],
)
def listar_evidencias(
    hallazgo_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Lista las evidencias del hallazgo con URL firmada."""
    try:
        return EvidenciaService(session).listar(hallazgo_id, usuario)
    except ValueError as error:
        raise _a_http_error(error) from error


@router.delete(
    "/evidencias/{evidencia_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def eliminar_evidencia(
    evidencia_id: int,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_active_user),
):
    """Elimina una evidencia del storage y de la base de datos."""
    try:
        EvidenciaService(session).eliminar(evidencia_id, usuario)
    except ValueError as error:
        raise _a_http_error(error) from error
