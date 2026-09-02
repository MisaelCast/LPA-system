"""Configuración del entorno de Alembic para SQLModel.

Alembic usa ``SQLModel.metadata`` como ``target_metadata`` para que las
migraciones reflejen exactamente los modelos de SQLModel. La URL de conexión
se obtiene de la configuración de la aplicación (variables de entorno), por lo
que no se almacenan credenciales en este repositorio.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

# Importa todos los modelos para que estén registrados en SQLModel.metadata
# antes de que Alembic los compare.
import app.models  # noqa: F401
from app.config import settings  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def _database_url() -> str:
    """Devuelve la URL de conexión desde la configuración de la app."""
    return settings.database_url


def run_migrations_offline() -> None:
    """Ejecuta migraciones en modo 'offline' (genera SQL sin conexión)."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecuta migraciones en modo 'online' (conexión real)."""
    connectable = engine_from_config(
        {"sqlalchemy.url": _database_url()},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
