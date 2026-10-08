from sqlmodel import Field, SQLModel


class UsuarioCelula(SQLModel, table=True):
    """Asigna usuarios a las células donde pueden operar (N:M)."""

    __tablename__ = "usuario_celula"

    usuario_id: int = Field(foreign_key="usuario.id", primary_key=True)
    celula_id: int = Field(foreign_key="celula.id", primary_key=True)