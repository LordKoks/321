"""
TheirStack API — 315k+ job sources (LinkedIn, Indeed, ATS systems).
Free tier: 200 credits/month ≈ 200 jobs.
Docs: https://theirstack.com
"""

from typing import Optional
import httpx

BASE_URL = "https://api.theirstack.com/v1/jobs/search"


class TheirStackClient:
    """Client for TheirStack Job Search API (200 free credits/month)."""

    def __init__(self, api_key: str, timeout: float = 15.0):
        """
        Args:
            api_key: TheirStack API key (set THEIRSTACK_API_KEY in env).
        """
        self.api_key = api_key
        self.timeout = timeout

    async def search_jobs(
        self,
        query: str,
        location: Optional[str] = None,
        remote: bool = True,
        page: int = 0,
        limit: int = 25,
    ) -> dict:
        """
        Search jobs via TheirStack.

        Args:
            query: job title or skill keywords.
            location: optional location string.
            remote: whether to filter for remote-only positions.
            page: 0-indexed page number.
            limit: results per page (max 100).

        Returns:
            Raw JSON response with jobs list and metadata.
        """
        payload: dict = {
            "query": query,
            "page": page,
            "limit": min(limit, 100),
            "remote": remote,
        }
        if location:
            payload["location"] = location

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(BASE_URL, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()
