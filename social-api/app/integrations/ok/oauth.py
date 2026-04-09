import hashlib
import urllib.parse
from typing import Optional
import httpx
from app.config import settings

OK_AUTH_URL = "https://connect.ok.ru/oauth/authorize"
OK_TOKEN_URL = "https://api.ok.ru/oauth/token.do"
OK_API_BASE = "https://api.ok.ru/api"


def get_ok_oauth_url(state: Optional[str] = None) -> str:
    params = {
        "client_id": settings.OK_APP_ID,
        "scope": "VALUABLE_ACCESS;LONG_ACCESS_TOKEN;GROUP_CONTENT",
        "response_type": "code",
        "redirect_uri": settings.OK_REDIRECT_URI,
    }
    if state:
        params["state"] = state
    return f"{OK_AUTH_URL}?{urllib.parse.urlencode(params)}"


async def exchange_ok_code(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            OK_TOKEN_URL,
            data={
                "code": code,
                "redirect_uri": settings.OK_REDIRECT_URI,
                "grant_type": "authorization_code",
                "client_id": settings.OK_APP_ID,
                "client_secret": settings.OK_APP_SECRET,
            },
        )
        resp.raise_for_status()
        return resp.json()


def compute_ok_sig(params: dict, session_secret_key: str) -> str:
    """Compute OK API signature."""
    sorted_params = "".join(f"{k}={v}" for k, v in sorted(params.items()))
    return hashlib.md5((sorted_params + session_secret_key).encode()).hexdigest()


def get_session_secret_key(access_token: str, app_secret: str) -> str:
    token_md5 = hashlib.md5(access_token.encode()).hexdigest()
    return hashlib.md5((token_md5 + app_secret).encode()).hexdigest()
