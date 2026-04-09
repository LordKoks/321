from abc import ABC, abstractmethod
from typing import Optional


class SocialIntegration(ABC):
    platform: str = ""

    @abstractmethod
    async def publish_post(
        self,
        token: str,
        content: str,
        media_urls: Optional[list[str]] = None,
        extra: Optional[dict] = None,
    ) -> str:
        """Publish post and return platform-specific post id."""

    @abstractmethod
    async def get_post_stats(
        self,
        token: str,
        post_id: str,
        extra: Optional[dict] = None,
    ) -> dict:
        """Return dict with keys: likes, views, shares, comments, reach."""

    @abstractmethod
    def get_oauth_url(self, state: Optional[str] = None) -> str:
        """Return OAuth authorization URL."""

    @abstractmethod
    async def exchange_code(self, code: str, state: Optional[str] = None) -> dict:
        """Exchange OAuth code for tokens. Returns dict with token info."""
