from collections.abc import Generator

from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, create_engine

from app.config import settings

# Registra los metadatos de SQLModel (necesario para que Alembic y los modelos
# compartan la misma instancia de metadata).
import app.models  # noqa: F401


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
