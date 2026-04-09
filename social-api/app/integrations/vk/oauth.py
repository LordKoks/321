import urllib.parse
from typing import Optional
import httpx
from app.config import settings


VK_OAUTH_URL = "https://oauth.vk.com/authorize"
VK_TOKEN_URL = "https://oauth.vk.com/access_token"
VK_SCOPE = "wall,photos,groups,offline"


def get_vk_oauth_url(state: Optional[str] = None, group_ids: Optional[str] = None) -> str:
    params = {
        "client_id": settings.VK_APP_ID,
        "redirect_uri": settings.VK_REDIRECT_URI,
        "scope": VK_SCOPE,
        "response_type": "code",
        "v": "5.199",
    }
    if state:
        params["state"] = state
    if group_ids:
        params["group_ids"] = group_ids
    return f"{VK_OAUTH_URL}?{urllib.parse.urlencode(params)}"


async def exchange_vk_code(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            VK_TOKEN_URL,
            params={
                "client_id": settings.VK_APP_ID,
                "client_secret": settings.VK_APP_SECRET,
                "redirect_uri": settings.VK_REDIRECT_URI,
                "code": code,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise ValueError(f"VK OAuth error: {data.get('error_description', data['error'])}")
        return data
