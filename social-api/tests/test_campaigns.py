"""Tests for /campaigns endpoints: CRUD, auth isolation."""

import pytest
from httpx import AsyncClient
from tests.conftest import register_and_login

pytestmark = pytest.mark.asyncio


async def _auth(client: AsyncClient, suffix: str = "") -> dict:
    return await register_and_login(client, f"user{suffix}@cmp.example.com", "password")


async def test_list_campaigns_empty(client: AsyncClient):
    h = await _auth(client, "1")
    r = await client.get("/campaigns/", headers=h)
    assert r.status_code == 200
    assert r.json() == []


async def test_create_campaign(client: AsyncClient):
    h = await _auth(client, "2")
    r = await client.post(
        "/campaigns/",
        json={"name": "Spring Sale", "budget": 500.0, "status": "draft"},
        headers=h,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Spring Sale"
    assert body["status"] == "draft"
    assert "id" in body


async def test_create_campaign_all_fields(client: AsyncClient):
    h = await _auth(client, "3")
    r = await client.post(
        "/campaigns/",
        json={
            "name": "Summer",
            "description": "A campaign",
            "start_date": "2026-06-01",
            "end_date": "2026-08-31",
            "budget": 1000.0,
            "status": "active",
        },
        headers=h,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["start_date"] == "2026-06-01"
    assert body["end_date"] == "2026-08-31"
    assert float(body["budget"]) == 1000.0


async def test_get_campaign(client: AsyncClient):
    h = await _auth(client, "4")
    created = (
        await client.post("/campaigns/", json={"name": "C1"}, headers=h)
    ).json()
    r = await client.get(f"/campaigns/{created['id']}", headers=h)
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


async def test_get_campaign_not_found(client: AsyncClient):
    h = await _auth(client, "5")
    r = await client.get("/campaigns/00000000-0000-0000-0000-000000000000", headers=h)
    assert r.status_code == 404


async def test_update_campaign(client: AsyncClient):
    h = await _auth(client, "6")
    created = (
        await client.post("/campaigns/", json={"name": "old name"}, headers=h)
    ).json()
    r = await client.patch(
        f"/campaigns/{created['id']}",
        json={"name": "new name", "status": "active"},
        headers=h,
    )
    assert r.status_code == 200
    assert r.json()["name"] == "new name"
    assert r.json()["status"] == "active"


async def test_delete_campaign(client: AsyncClient):
    h = await _auth(client, "7")
    created = (
        await client.post("/campaigns/", json={"name": "to delete"}, headers=h)
    ).json()
    r = await client.delete(f"/campaigns/{created['id']}", headers=h)
    assert r.status_code == 204
    r2 = await client.get(f"/campaigns/{created['id']}", headers=h)
    assert r2.status_code == 404


async def test_campaign_isolation(client: AsyncClient):
    h_a = await _auth(client, "8a")
    h_b = await _auth(client, "8b")
    created = (
        await client.post("/campaigns/", json={"name": "private"}, headers=h_a)
    ).json()
    r = await client.get(f"/campaigns/{created['id']}", headers=h_b)
    assert r.status_code == 404


async def test_campaigns_require_auth(client: AsyncClient):
    r = await client.get("/campaigns/")
    assert r.status_code == 401


async def test_campaign_statuses(client: AsyncClient):
    h = await _auth(client, "9")
    for status in ("draft", "active", "paused", "completed"):
        r = await client.post("/campaigns/", json={"name": f"c-{status}", "status": status}, headers=h)
        assert r.status_code == 201
        assert r.json()["status"] == status
