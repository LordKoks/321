import io
import httpx
from typing import Optional
from app.integrations.base import SocialIntegration
from app.core.media_uploader import download_media

YT_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
YT_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"


class YouTubeIntegration(SocialIntegration):
    platform = "youtube"

    def get_oauth_url(self, state: Optional[str] = None) -> str:
        from app.integrations.youtube.oauth import get_youtube_oauth_url
        return get_youtube_oauth_url(state)

    async def exchange_code(self, code: str, state: Optional[str] = None) -> dict:
        from app.integrations.youtube.oauth import exchange_google_code
        return await exchange_google_code(code)

    async def publish_post(
        self,
        token: str,
        content: str,
        media_urls: Optional[list[str]] = None,
        extra: Optional[dict] = None,
    ) -> str:
        extra = extra or {}
        if not media_urls:
            raise ValueError("YouTube requires a video URL")

        video_url = media_urls[0]
        video_data, content_type = await download_media(video_url)

        metadata = {
            "snippet": {
                "title": extra.get("title", content[:100]),
                "description": content,
                "categoryId": extra.get("category_id", "22"),
            },
            "status": {
                "privacyStatus": extra.get("privacy_status", "public"),
            },
        }

        import json
        boundary = "----YouTubeUploadBoundary"
        body_parts = [
            f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode(),
            json.dumps(metadata).encode(),
            f"\r\n--{boundary}\r\nContent-Type: {content_type}\r\n\r\n".encode(),
            video_data,
            f"\r\n--{boundary}--".encode(),
        ]
        body = b"".join(body_parts)

        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(
                YT_UPLOAD_URL,
                content=body,
                params={"uploadType": "multipart", "part": "snippet,status"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": f"multipart/related; boundary={boundary}",
                },
            )
            resp.raise_for_status()
            return resp.json()["id"]

    async def get_post_stats(
        self, token: str, post_id: str, extra: Optional[dict] = None
    ) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                YT_VIDEO_URL,
                params={"id": post_id, "part": "statistics"},
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            stats = items[0].get("statistics", {}) if items else {}
            return {
                "likes": int(stats.get("likeCount", 0)),
                "views": int(stats.get("viewCount", 0)),
                "shares": 0,
                "comments": int(stats.get("commentCount", 0)),
                "reach": int(stats.get("viewCount", 0)),
            }


youtube_integration = YouTubeIntegration()
