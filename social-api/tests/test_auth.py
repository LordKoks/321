"""Tests for /auth endpoints: register, login, refresh."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_register_success(client: AsyncClient):
    resp = await client.post(
        "/auth/register", json={"email": "alice@example.com", "password": "secret123"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


async def test_register_duplicate_email(client: AsyncClient):
    payload = {"email": "bob@example.com", "password": "secret123"}
    r1 = await client.post("/auth/register", json=payload)
    assert r1.status_code == 201
    r2 = await client.post("/auth/register", json=payload)
    assert r2.status_code == 400
    assert "already registered" in r2.json()["detail"].lower()


async def test_login_success(client: AsyncClient):
    await client.post(
        "/auth/register", json={"email": "carol@example.com", "password": "pw1234"}
    )
    resp = await client.post(
        "/auth/login", data={"username": "carol@example.com", "password": "pw1234"}
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/auth/register", json={"email": "dave@example.com", "password": "correct"}
    )
    resp = await client.post(
        "/auth/login", data={"username": "dave@example.com", "password": "wrong"}
    )
    assert resp.status_code == 401


async def test_login_unknown_user(client: AsyncClient):
    resp = await client.post(
        "/auth/login", data={"username": "nobody@example.com", "password": "x"}
    )
    assert resp.status_code == 401


async def test_refresh_token(client: AsyncClient):
    r = await client.post(
        "/auth/register", json={"email": "eve@example.com", "password": "pw"}
    )
    refresh = r.json()["refresh_token"]
    resp = await client.post("/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_refresh_invalid_token(client: AsyncClient):
    resp = await client.post("/auth/refresh", json={"refresh_token": "not.a.token"})
    assert resp.status_code == 401


async def test_access_token_rejects_refresh_token(client: AsyncClient):
    """A refresh token must NOT be accepted as an access token for protected routes."""
    r = await client.post(
        "/auth/register", json={"email": "frank@example.com", "password": "pw"}
    )
    refresh = r.json()["refresh_token"]
    resp = await client.get(
        "/posts/", headers={"Authorization": f"Bearer {refresh}"}
    )
    assert resp.status_code == 401
