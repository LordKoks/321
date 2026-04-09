import httpx
from typing import Optional
from app.integrations.base import SocialIntegration
from app.core.media_uploader import download_media

X_API_BASE = "https://api.twitter.com/2"
X_UPLOAD_URL = "https://upload.twitter.com/1.1/media/upload.json"


class XIntegration(SocialIntegration):
    platform = "x"

    def get_oauth_url(self, state: Optional[str] = None) -> str:
        from app.integrations.x.oauth import get_x_oauth_url
        url, _ = get_x_oauth_url(state or "default")
        return url

    async def exchange_code(self, code: str, state: Optional[str] = None) -> dict:
        raise NotImplementedError("Use exchange_x_code directly with code_verifier")

    async def _upload_media(self, token: str, image_data: bytes, content_type: str) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                X_UPLOAD_URL,
                files={"media": ("media", image_data, content_type)},
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            return str(resp.json()["media_id_string"])

    async def publish_post(
        self,
        token: str,
        content: str,
        media_urls: Optional[list[str]] = None,
        extra: Optional[dict] = None,
    ) -> str:
        payload: dict = {"text": content}
        media_ids = []
        for url in media_urls or []:
            data, ct = await download_media(url)
            media_id = await self._upload_media(token, data, ct)
            media_ids.append(media_id)
        if media_ids:
            payload["media"] = {"media_ids": media_ids}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{X_API_BASE}/tweets",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["data"]["id"]

    async def get_post_stats(
        self, token: str, post_id: str, extra: Optional[dict] = None
    ) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{X_API_BASE}/tweets/{post_id}",
                params={"tweet.fields": "public_metrics"},
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            metrics = resp.json().get("data", {}).get("public_metrics", {})
            return {
                "likes": metrics.get("like_count", 0),
                "views": metrics.get("impression_count", 0),
                "shares": metrics.get("retweet_count", 0),
                "comments": metrics.get("reply_count", 0),
                "reach": metrics.get("impression_count", 0),
            }


x_integration = XIntegration()
