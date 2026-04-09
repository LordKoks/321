"""Tests for /accounts endpoints: list, delete, OAuth URL stubs, Telegram stubs."""

import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
from tests.conftest import register_and_login

pytestmark = pytest.mark.asyncio


async def _auth(client: AsyncClient, suffix: str = "") -> dict:
    return await register_and_login(client, f"user{suffix}@accts.example.com", "password")


async def test_list_accounts_empty(client: AsyncClient):
    h = await _auth(client, "1")
    r = await client.get("/accounts/", headers=h)
    assert r.status_code == 200
    assert r.json() == []


async def test_delete_account_not_found(client: AsyncClient):
    h = await _auth(client, "2")
    r = await client.delete(
        f"/accounts/00000000-0000-0000-0000-000000000000", headers=h
    )
    assert r.status_code == 404


async def test_accounts_require_auth(client: AsyncClient):
    r = await client.get("/accounts/")
    assert r.status_code == 401


# ── OAuth connect endpoints return a redirect URL ─────────────────────────

async def test_vk_connect_returns_url(client: AsyncClient):
    h = await _auth(client, "vk1")
    with patch("app.routers.accounts.VKOAuth") as MockOAuth:
        instance = MockOAuth.return_value
        instance.get_auth_url.return_value = "https://oauth.vk.com/authorize?client_id=test"
        r = await client.get("/accounts/vk/connect", headers=h)
    assert r.status_code == 200
    assert "url" in r.json()


async def test_x_connect_returns_url_and_verifier(client: AsyncClient):
    h = await _auth(client, "x1")
    with patch("app.routers.accounts.XOAuth") as MockOAuth:
        instance = MockOAuth.return_value
        instance.get_auth_url.return_value = ("https://twitter.com/i/oauth2/authorize", "verifier123")
        r = await client.get("/accounts/x/connect", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert "url" in body
    assert "code_verifier" in body


async def test_ok_connect_returns_url(client: AsyncClient):
    h = await _auth(client, "ok1")
    with patch("app.routers.accounts.OKOAuth") as MockOAuth:
        instance = MockOAuth.return_value
        instance.get_auth_url.return_value = "https://connect.ok.ru/oauth/authorize?client_id=test"
        r = await client.get("/accounts/ok/connect", headers=h)
    assert r.status_code == 200
    assert "url" in r.json()


async def test_youtube_connect_returns_url(client: AsyncClient):
    h = await _auth(client, "yt1")
    with patch("app.routers.accounts.YouTubeOAuth") as MockOAuth:
        instance = MockOAuth.return_value
        instance.get_auth_url.return_value = "https://accounts.google.com/o/oauth2/auth?client_id=test"
        r = await client.get("/accounts/youtube/connect", headers=h)
    assert r.status_code == 200
    assert "url" in r.json()


# ── OAuth callback endpoints create a SocialAccount ───────────────────────

async def test_vk_callback_creates_account(client: AsyncClient):
    """Simulate VK OAuth callback creating a linked account."""
    with patch("app.routers.accounts.VKOAuth") as MockOAuth:
        instance = MockOAuth.return_value
        instance.exchange_code = AsyncMock(
            return_value={"access_token": "vk_tok", "user_id": 12345}
        )
        # We need a real user_id to pass as state
        reg = await client.post(
            "/auth/register",
            json={"email": "vk_cb@accts.example.com", "password": "pw"},
        )
        user_id = _decode_user_id(reg.json()["access_token"])
        r = await client.get(
            f"/accounts/vk/callback?code=abc&state={user_id}"
        )
    assert r.status_code == 200
    assert r.json()["platform"] == "vk"


async def test_ok_callback_creates_account(client: AsyncClient):
    with patch("app.routers.accounts.OKOAuth") as MockOAuth:
        instance = MockOAuth.return_value
        instance.exchange_code = AsyncMock(
            return_value={"access_token": "ok_tok", "uid": 99999}
        )
        reg = await client.post(
            "/auth/register",
            json={"email": "ok_cb@accts.example.com", "password": "pw"},
        )
        user_id = _decode_user_id(reg.json()["access_token"])
        r = await client.get(
            f"/accounts/ok/callback?code=abc&state={user_id}"
        )
    assert r.status_code == 200
    assert r.json()["platform"] == "ok"


async def test_youtube_callback_creates_account(client: AsyncClient):
    with patch("app.routers.accounts.YouTubeOAuth") as MockOAuth:
        instance = MockOAuth.return_value
        instance.exchange_code = AsyncMock(
            return_value={
                "access_token": "yt_tok",
                "refresh_token": "yt_refresh",
                "sub": "google_user_123",
            }
        )
        reg = await client.post(
            "/auth/register",
            json={"email": "yt_cb@accts.example.com", "password": "pw"},
        )
        user_id = _decode_user_id(reg.json()["access_token"])
        r = await client.get(
            f"/accounts/youtube/callback?code=abc&state={user_id}"
        )
    assert r.status_code == 200
    assert r.json()["platform"] == "youtube"


async def test_delete_account_success(client: AsyncClient):
    """Create an account manually and then delete it."""
    with patch("app.routers.accounts.VKOAuth") as MockOAuth:
        instance = MockOAuth.return_value
        instance.exchange_code = AsyncMock(
            return_value={"access_token": "vk_tok2", "user_id": 55555}
        )
        reg = await client.post(
            "/auth/register",
            json={"email": "del_acct@accts.example.com", "password": "pw"},
        )
        user_id = _decode_user_id(reg.json()["access_token"])
        h = {"Authorization": f"Bearer {reg.json()['access_token']}"}
        await client.get(f"/accounts/vk/callback?code=abc&state={user_id}")
        # Now list and delete
        accts = (await client.get("/accounts/", headers=h)).json()
        assert len(accts) == 1
        r = await client.delete(f"/accounts/{accts[0]['id']}", headers=h)
        assert r.status_code == 204
        accts2 = (await client.get("/accounts/", headers=h)).json()
        assert accts2 == []


# ── Telegram phone-auth endpoints ─────────────────────────────────────────

async def test_telegram_send_code(client: AsyncClient):
    h = await _auth(client, "tg1")
    with patch(
        "app.integrations.telegram.api.telegram_integration.start_phone_auth",
        new_callable=AsyncMock,
        return_value={"session": "session_str", "phone_code_hash": "abc123"},
    ):
        r = await client.post(
            "/accounts/telegram/send-code",
            json={"phone": "+79991234567"},
            headers=h,
        )
    assert r.status_code == 200
    body = r.json()
    assert body["session"] == "session_str"
    assert body["phone_code_hash"] == "abc123"


async def test_telegram_verify(client: AsyncClient):
    reg = await client.post(
        "/auth/register",
        json={"email": "tg_verify@accts.example.com", "password": "pw"},
    )
    h = {"Authorization": f"Bearer {reg.json()['access_token']}"}
    with patch(
        "app.integrations.telegram.api.telegram_integration.complete_phone_auth",
        new_callable=AsyncMock,
        return_value="completed_session_string",
    ):
        r = await client.post(
            "/accounts/telegram/verify",
            json={
                "phone": "+79991234567",
                "code": "12345",
                "session": "session_str",
                "phone_code_hash": "abc123",
            },
            headers=h,
        )
    assert r.status_code == 200
    assert r.json()["platform"] == "telegram"


# ── helper ─────────────────────────────────────────────────────────────────

def _decode_user_id(token: str) -> str:
    import base64, json
    payload_b64 = token.split(".")[1]
    # Add padding
    padding = 4 - len(payload_b64) % 4
    payload_b64 += "=" * (padding % 4)
    decoded = json.loads(base64.urlsafe_b64decode(payload_b64))
    return decoded["sub"]
