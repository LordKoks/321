"""Tests for /analytics endpoint."""

import pytest
import uuid
from datetime import date
from httpx import AsyncClient
from tests.conftest import register_and_login

pytestmark = pytest.mark.asyncio


async def test_analytics_empty(client: AsyncClient):
    h = await register_and_login(client, "user1@analytics.example.com", "pw")
    r = await client.get("/analytics/", headers=h)
    assert r.status_code == 200
    assert r.json() == []


async def test_analytics_requires_auth(client: AsyncClient):
    r = await client.get("/analytics/")
    assert r.status_code == 401


async def test_analytics_filter_by_account(client: AsyncClient):
    """Filter analytics by a non-existent account_id returns empty list."""
    h = await register_and_login(client, "user2@analytics.example.com", "pw")
    r = await client.get(
        f"/analytics/?account_id=00000000-0000-0000-0000-000000000000", headers=h
    )
    assert r.status_code == 200
    assert r.json() == []


async def test_analytics_isolation(client: AsyncClient):
    """User A cannot see User B's analytics rows."""
    h_a = await register_and_login(client, "ana@analytics.example.com", "pw")
    h_b = await register_and_login(client, "anb@analytics.example.com", "pw")

    # Inject an analytics row for user A via DB
    from tests.conftest import TestSessionLocal
    from app.models.social_account import SocialAccount, Platform
    from app.models.analytics import Analytics

    async with TestSessionLocal() as db:
        acct = SocialAccount(
            user_id=_get_user_id(h_a),
            platform=Platform.vk,
            account_id="vk123",
            encrypted_token="tok",
        )
        db.add(acct)
        await db.flush()
        row = Analytics(
            social_account_id=acct.id,
            date=date.today(),
            likes=10,
            views=100,
            shares=5,
            comments=2,
            reach=80,
        )
        db.add(row)
        await db.commit()

    r_a = await client.get("/analytics/", headers=h_a)
    r_b = await client.get("/analytics/", headers=h_b)

    assert r_a.status_code == 200
    assert len(r_a.json()) == 1
    assert r_b.status_code == 200
    assert r_b.json() == []


def _get_user_id(auth_header: dict) -> uuid.UUID:
    token = auth_header["Authorization"].split(" ")[1]
    import base64, json as _json
    payload_b64 = token.split(".")[1]
    payload_b64 += "=" * (4 - len(payload_b64) % 4)
    decoded = _json.loads(base64.urlsafe_b64decode(payload_b64))
    return uuid.UUID(decoded["sub"])
