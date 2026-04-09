import io
import httpx
from typing import Optional


async def download_media(url: str) -> tuple[bytes, str]:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "image/jpeg")
        return resp.content, content_type


def get_mime_type(url: str) -> str:
    lower = url.lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".gif"):
        return "image/gif"
    if lower.endswith(".mp4"):
        return "video/mp4"
    if lower.endswith(".mov"):
        return "video/quicktime"
    return "image/jpeg"


def split_media_urls(media_urls: list[str]) -> tuple[list[str], list[str]]:
    images, videos = [], []
    for url in media_urls or []:
        mime = get_mime_type(url)
        if mime.startswith("video"):
            videos.append(url)
        else:
            images.append(url)
    return images, videos
