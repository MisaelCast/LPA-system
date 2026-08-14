from collections.abc import Generator

from sqlalchemy import inspect, text
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

# Registra los metadatos de SQLModel antes de ejecutar create_all.
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


def create_db_and_tables() -> None:
    """Crea las tablas una vez registrados los modelos de SQLModel."""
    if not SQLModel.metadata.tables:
        return

    SQLModel.metadata.create_all(engine)


def ensure_schema_migrations() -> None:
    """Aplica migraciones incrementales de forma idempotente."""
    inspector = inspect(engine)

    _add_column_if_missing(
        inspector, "ejecucion_auditoria", "estado",
        "ALTER TABLE ejecucion_auditoria ADD COLUMN estado VARCHAR(20) NOT NULL DEFAULT 'en_proceso'",
    )

    _add_unique_constraint_if_missing(
        inspector, "respuesta", "uq_respuesta_ejecucion_criterio",
        "ejecucion_auditoria_id, criterio_id",
    )


def _add_column_if_missing(
    inspector, table: str, column: str, sql: str
) -> None:
    columns = {col["name"] for col in inspector.get_columns(table)}
    if column not in columns:
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()


def _add_unique_constraint_if_missing(
    inspector, table: str, constraint_name: str, columns: str
) -> None:
    constraints = inspector.get_unique_constraints(table)
    names = {c["name"] for c in constraints}
    if constraint_name not in names:
        with engine.connect() as conn:
            conn.execute(text(
                f"ALTER TABLE {table} ADD CONSTRAINT {constraint_name} "
                f"UNIQUE ({columns})"
            ))
            conn.commit()
