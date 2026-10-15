"""Fixtures compartidos para las pruebas de integración HTTP."""

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    """Cliente de pruebas contra la API en ejecución."""
    # Las pruebas que usan este fixture asumen que la base de datos
    # de desarrollo está poblada (migraciones + seed ejecutados).
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
