from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.models.hallazgo_responsable import HallazgoResponsable
from app.models.usuario_area import UsuarioArea

if TYPE_CHECKING:
    from app.models.area import Area
    from app.models.ejecucion_auditoria import EjecucionAuditoria
    from app.models.hallazgo import Hallazgo
    from app.models.rol import Rol


class Usuario(SQLModel, table=True):
    """Persona que utiliza el sistema LPA."""

    __tablename__ = "usuario"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=150)
    correo: str = Field(max_length=255, unique=True, index=True)
    contrasena_hash: str = Field(max_length=255)
    activo: bool = Field(default=True)
    rol_id: int = Field(foreign_key="rol.id")

    rol: "Rol" = Relationship(back_populates="usuarios")
    areas: list["Area"] = Relationship(
        back_populates="usuarios",
        link_model=UsuarioArea,
    )
    ejecuciones_auditoria: list["EjecucionAuditoria"] = Relationship(
        back_populates="usuario",
    )
    hallazgos_responsables: list["Hallazgo"] = Relationship(
        back_populates="responsables",
        link_model=HallazgoResponsable,
    )

    @property
    def rol_nombre(self) -> str:
        """Nombre del rol asociado al usuario."""
        return self.rol.nombre if self.rol else ""
