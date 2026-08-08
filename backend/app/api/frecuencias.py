"""Endpoints para listado de frecuencias."""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.auth.permissions import require_roles
from app.db.database import get_session
from app.models.frecuencia import Frecuencia
from app.models.usuario import Usuario
from app.schemas.frecuencia import FrecuenciaRead
from app.services.frecuencia_service import FrecuenciaService

router = APIRouter(tags=["frecuencias"])


@router.get("/frecuencias", response_model=list[FrecuenciaRead])
def listar_frecuencias(
    session: Session = Depends(get_session),
    _: Usuario = Depends(require_roles("Administrador")),
) -> list[Frecuencia]:
    """Lista todas las frecuencias disponibles.

    Solo accesible por usuarios con rol **Administrador**.
    """
    return FrecuenciaService(session).listar()
