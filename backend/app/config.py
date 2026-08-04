from sqlalchemy.engine import URL
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "LPA System API"
    app_description: str = "Backend API for LPA System."
    app_version: str = "0.1.0"
    environment: str = "development"

    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "lpa_system"
    database_user: str = "postgres"
    database_password: str = "postgres"

    # Development-only default — override via SECRET_KEY in .env for production.
    secret_key: str = "development-secret-key-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    backend_cors_origins: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        """Orígenes permitidos para CORS a partir de la variable separada por comas."""
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def database_url(self) -> str:
        """Build the PostgreSQL connection URL from environment settings."""
        url = URL.create(
            drivername="postgresql+psycopg",
            username=self.database_user,
            password=self.database_password,
            host=self.database_host,
            port=self.database_port,
            database=self.database_name,
        )
        return url.render_as_string(hide_password=False)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
