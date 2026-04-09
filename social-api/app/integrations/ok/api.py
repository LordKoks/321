import httpx
import json
from typing import Optional
from app.integrations.base import SocialIntegration
from app.config import settings

OK_API_BASE = "https://api.ok.ru/api"


class OKIntegration(SocialIntegration):
    platform = "ok"

    def get_oauth_url(self, state: Optional[str] = None) -> str:
        from app.integrations.ok.oauth import get_ok_oauth_url
        return get_ok_oauth_url(state)

    async def exchange_code(self, code: str, state: Optional[str] = None) -> dict:
        from app.integrations.ok.oauth import exchange_ok_code
        return await exchange_ok_code(code)

    def _build_params(self, token: str, method: str, extra_params: dict) -> dict:
        from app.integrations.ok.oauth import compute_ok_sig, get_session_secret_key
        params = {
            "application_key": settings.OK_PUBLIC_KEY,
            "format": "json",
            "method": method,
            **extra_params,
        }
        session_key = get_session_secret_key(token, settings.OK_APP_SECRET)
        sig = compute_ok_sig(params, session_key)
        params["sig"] = sig
        params["access_token"] = token
        return params

    async def publish_post(
        self,
        token: str,
        content: str,
        media_urls: Optional[list[str]] = None,
        extra: Optional[dict] = None,
    ) -> str:
        extra = extra or {}
        attachment = {"media": [{"type": "text", "text": content}]}

        if media_urls:
            attachment["media"].extend(
                [{"type": "photo", "list": [{"url": url}]} for url in media_urls]
            )

        method_params = {
            "type": "GROUP_THEME" if extra.get("group_id") else "USER",
            "attachment": json.dumps(attachment),
        }
        if extra.get("group_id"):
            method_params["gid"] = extra["group_id"]

        params = self._build_params(token, "mediatopic.post", method_params)
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{OK_API_BASE}/mediatopic/post", params=params)
            resp.raise_for_status()
            data = resp.json()
            if "error_code" in data:
                raise ValueError(f"OK API error: {data.get('error_msg')}")
            return str(data.get("id", ""))

    async def get_post_stats(
        self, token: str, post_id: str, extra: Optional[dict] = None
    ) -> dict:
        params = self._build_params(token, "mediatopic.getInfo", {"topic_id": post_id})
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{OK_API_BASE}/mediatopic/getInfo", params=params)
            resp.raise_for_status()
            data = resp.json()
            likes = data.get("like_count", 0)
            views = data.get("view_count", 0)
            comments = data.get("discussion_summary", {}).get("comments_count", 0)
            return {"likes": likes, "views": views, "shares": 0, "comments": comments, "reach": views}


ok_integration = OKIntegration()
