"""Tests for /posts endpoints: CRUD, auth isolation."""

import pytest
from httpx import AsyncClient
from tests.conftest import register_and_login

pytestmark = pytest.mark.asyncio


async def _auth(client: AsyncClient, suffix: str = "") -> dict:
    return await register_and_login(client, f"user{suffix}@posts.example.com", "password")


async def test_list_posts_empty(client: AsyncClient):
    h = await _auth(client, "1")
    r = await client.get("/posts/", headers=h)
    assert r.status_code == 200
    assert r.json() == []


async def test_create_post_draft(client: AsyncClient):
    h = await _auth(client, "2")
    r = await client.post(
        "/posts/",
        json={"content": "Hello world", "media_urls": [], "target_account_ids": []},
        headers=h,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["content"] == "Hello world"
    assert body["status"] == "draft"
    assert "id" in body


async def test_create_post_scheduled(client: AsyncClient):
    h = await _auth(client, "3")
    r = await client.post(
        "/posts/",
        json={
            "content": "Scheduled post",
            "scheduled_at": "2099-01-01T12:00:00Z",
            "target_account_ids": [],
        },
        headers=h,
    )
    assert r.status_code == 201
    assert r.json()["status"] == "scheduled"


async def test_get_post(client: AsyncClient):
    h = await _auth(client, "4")
    created = (
        await client.post("/posts/", json={"content": "test", "target_account_ids": []}, headers=h)
    ).json()
    r = await client.get(f"/posts/{created['id']}", headers=h)
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


async def test_get_post_not_found(client: AsyncClient):
    h = await _auth(client, "5")
    r = await client.get("/posts/00000000-0000-0000-0000-000000000000", headers=h)
    assert r.status_code == 404


async def test_update_post(client: AsyncClient):
    h = await _auth(client, "6")
    created = (
        await client.post("/posts/", json={"content": "old", "target_account_ids": []}, headers=h)
    ).json()
    r = await client.patch(
        f"/posts/{created['id']}", json={"content": "new content"}, headers=h
    )
    assert r.status_code == 200
    assert r.json()["content"] == "new content"


async def test_delete_post(client: AsyncClient):
    h = await _auth(client, "7")
    created = (
        await client.post("/posts/", json={"content": "bye", "target_account_ids": []}, headers=h)
    ).json()
    r = await client.delete(f"/posts/{created['id']}", headers=h)
    assert r.status_code == 204
    # Confirm it's gone
    r2 = await client.get(f"/posts/{created['id']}", headers=h)
    assert r2.status_code == 404


async def test_post_isolation_between_users(client: AsyncClient):
    """User A cannot see User B's posts."""
    h_a = await _auth(client, "8a")
    h_b = await _auth(client, "8b")
    created = (
        await client.post("/posts/", json={"content": "private", "target_account_ids": []}, headers=h_a)
    ).json()
    r = await client.get(f"/posts/{created['id']}", headers=h_b)
    assert r.status_code == 404


async def test_post_requires_auth(client: AsyncClient):
    r = await client.get("/posts/")
    assert r.status_code == 401


async def test_post_list_contains_created(client: AsyncClient):
    h = await _auth(client, "9")
    await client.post("/posts/", json={"content": "p1", "target_account_ids": []}, headers=h)
    await client.post("/posts/", json={"content": "p2", "target_account_ids": []}, headers=h)
    r = await client.get("/posts/", headers=h)
    assert r.status_code == 200
    titles = [p["content"] for p in r.json()]
    assert "p1" in titles
    assert "p2" in titles


async def test_invalid_account_id_in_post(client: AsyncClient):
    """Creating a post with a non-existent account ID returns 404."""
    h = await _auth(client, "10")
    r = await client.post(
        "/posts/",
        json={
            "content": "x",
            "target_account_ids": ["00000000-0000-0000-0000-000000000099"],
        },
        headers=h,
    )
    assert r.status_code == 404
