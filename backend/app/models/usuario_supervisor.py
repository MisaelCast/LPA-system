from sqlmodel import Field, SQLModel


class UsuarioSupervisor(SQLModel, table=True):
    """Relaciona a un Gerente con los Supervisores a su cargo (N:M)."""

    __tablename__ = "usuario_supervisor"

    gerente_id: int = Field(foreign_key="usuario.id", primary_key=True)
    supervisor_id: int = Field(foreign_key="usuario.id", primary_key=True)