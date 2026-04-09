import httpx
from typing import Optional
from app.integrations.base import SocialIntegration
from app.core.media_uploader import download_media

VK_API_BASE = "https://api.vk.com/method"
VK_VERSION = "5.199"


class VKIntegration(SocialIntegration):
    platform = "vk"

    def get_oauth_url(self, state: Optional[str] = None) -> str:
        from app.integrations.vk.oauth import get_vk_oauth_url
        return get_vk_oauth_url(state)

    async def exchange_code(self, code: str, state: Optional[str] = None) -> dict:
        from app.integrations.vk.oauth import exchange_vk_code
        return await exchange_vk_code(code)

    async def _upload_photo(self, token: str, image_data: bytes, content_type: str) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{VK_API_BASE}/photos.getWallUploadServer",
                params={"access_token": token, "v": VK_VERSION},
            )
            resp.raise_for_status()
            upload_url = resp.json()["response"]["upload_url"]

            upload_resp = await client.post(
                upload_url,
                files={"photo": ("photo.jpg", image_data, content_type)},
            )
            upload_resp.raise_for_status()
            upload_data = upload_resp.json()

            save_resp = await client.post(
                f"{VK_API_BASE}/photos.saveWallPhoto",
                params={
                    "access_token": token,
                    "v": VK_VERSION,
                    "photo": upload_data["photo"],
                    "server": upload_data["server"],
                    "hash": upload_data["hash"],
                },
            )
            save_resp.raise_for_status()
            photo = save_resp.json()["response"][0]
            return f"photo{photo['owner_id']}_{photo['id']}"

    async def publish_post(
        self,
        token: str,
        content: str,
        media_urls: Optional[list[str]] = None,
        extra: Optional[dict] = None,
    ) -> str:
        attachments = []
        for url in media_urls or []:
            image_data, content_type = await download_media(url)
            att = await self._upload_photo(token, image_data, content_type)
            attachments.append(att)

        extra = extra or {}
        params: dict = {
            "access_token": token,
            "v": VK_VERSION,
            "message": content,
            "from_group": extra.get("from_group", 0),
        }
        if extra.get("owner_id"):
            params["owner_id"] = extra["owner_id"]
        if attachments:
            params["attachments"] = ",".join(attachments)

        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{VK_API_BASE}/wall.post", params=params)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                raise ValueError(f"VK wall.post error: {data['error']['error_msg']}")
            return str(data["response"]["post_id"])

    async def get_post_stats(
        self, token: str, post_id: str, extra: Optional[dict] = None
    ) -> dict:
        extra = extra or {}
        owner_id = extra.get("owner_id", "")
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{VK_API_BASE}/wall.getById",
                params={
                    "access_token": token,
                    "v": VK_VERSION,
                    "posts": f"{owner_id}_{post_id}",
                    "extended": 1,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            post = data.get("response", {}).get("items", [{}])[0]
            likes = post.get("likes", {}).get("count", 0)
            views = post.get("views", {}).get("count", 0)
            shares = post.get("reposts", {}).get("count", 0)
            comments = post.get("comments", {}).get("count", 0)
            return {"likes": likes, "views": views, "shares": shares, "comments": comments, "reach": views}


vk_integration = VKIntegration()
