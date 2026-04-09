"""
SerpApi — Google Jobs aggregator.
Free tier: 100 searches/month.
Docs: https://serpapi.com/google-jobs-api
"""

from typing import Optional
import httpx

BASE_URL = "https://serpapi.com/search"


class SerpApiClient:
    """Client for SerpApi Google Jobs search (100 free searches/month)."""

    def __init__(self, api_key: str, timeout: float = 15.0):
        """
        Args:
            api_key: SerpApi API key (set SERPAPI_KEY in env).
        """
        self.api_key = api_key
        self.timeout = timeout

    async def search_jobs(
        self,
        query: str,
        location: Optional[str] = None,
        language: str = "en",
        start: int = 0,
    ) -> dict:
        """
        Search Google Jobs via SerpApi.

        Args:
            query: job title / keywords.
            location: location string, e.g. "New York, NY".
            language: ISO language code.
            start: pagination offset (multiples of 10).

        Returns:
            Raw JSON response with jobs_results list.
        """
        params: dict = {
            "engine": "google_jobs",
            "q": query,
            "hl": language,
            "api_key": self.api_key,
            "start": start,
        }
        if location:
            params["location"] = location

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(BASE_URL, params=params)
            resp.raise_for_status()
            return resp.json()
