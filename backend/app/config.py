import json

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

    default_admin_password: str = "admin123"

    backend_cors_origins: str = ""

    def _parse_origins_as_json(self, raw: str) -> list[str] | None:
        """Intenta interpretar la cadena como una lista JSON de orígenes."""
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

        if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
            return [item.strip() for item in parsed if item.strip()]
        return None

    def _parse_origins_as_csv(self, raw: str) -> list[str]:
        """Interpreta la cadena como orígenes separados por coma."""
        return [
            origin.strip()
            for origin in raw.split(",")
            if origin.strip()
        ]

    @property
    def cors_origins_list(self) -> list[str]:
        """Orígenes permitidos para CORS.

        Soporta tanto formato CSV (separado por comas) como JSON (lista de cadenas).
        """
        if not self.backend_cors_origins:
            return []

        json_origins = self._parse_origins_as_json(self.backend_cors_origins)
        if json_origins is not None:
            return json_origins

        return self._parse_origins_as_csv(self.backend_cors_origins)

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
