"""Pruebas de autenticación: login, refresh token y validación."""

from datetime import timedelta

import pytest
from sqlmodel import Session

from app.auth.jwt import create_access_token, create_refresh_token
from app.models.usuario import Usuario


def _login_admin(client) -> dict:
    response = client.post(
        "/auth/login",
        json={"correo": "admin@lpa.com", "contrasena": "Admin123*"},
    )
    assert response.status_code == 200, response.text
    return response.json()


class TestLogin:
    def test_login_devuelve_tokens(self, client):
        data = _login_admin(client)
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    def test_login_credenciales_invalidas(self, client):
        response = client.post(
            "/auth/login",
            json={"correo": "admin@lpa.com", "contrasena": "incorrecta"},
        )
        assert response.status_code == 401


class TestRefresh:
    def test_refresh_con_token_valido(self, client):
        tokens = _login_admin(client)
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # El nuevo access token es válido para acceder a endpoints protegidos.
        me = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {data['access_token']}"},
        )
        assert me.status_code == 200
        assert me.json()["correo"] == "admin@lpa.com"

    def test_refresh_con_token_invalido(self, client):
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "no-es-un-jwt"},
        )
        assert response.status_code == 401

    def test_refresh_con_access_token_rechaza(self, client):
        tokens = _login_admin(client)
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": tokens["access_token"]},
        )
        assert response.status_code == 401
        assert "inv" in response.json()["detail"].lower()

    def test_refresh_expirado(self, client):
        from app.config import settings
        import jwt

        token = create_access_token(
            subject="1", expires_delta=timedelta(seconds=-10)
        )
        response = client.post(
            "/auth/refresh", json={"refresh_token": token}
        )
        assert response.status_code == 401
        assert "expir" in response.json()["detail"].lower()


class TestProtectedEndpoint:
    def test_token_expirado_retorna_401(self, client):
        token = create_access_token(
            subject="1", expires_delta=timedelta(seconds=-10)
        )
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    def test_token_valido_retorna_usuario(self, client):
        tokens = _login_admin(client)
        response = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert response.status_code == 200
        assert response.json()["correo"] == "admin@lpa.com"
