"""
Glassdoor Job Search via RapidAPI — 100 free requests/month.
Requires RAPIDAPI_KEY env var.
Host: glassdoor-job-search.p.rapidapi.com
"""

from typing import Optional
import httpx

BASE_URL = "https://glassdoor-job-search.p.rapidapi.com/api/search"
RAPIDAPI_HOST = "glassdoor-job-search.p.rapidapi.com"


class GlassdoorClient:
    """Client for the Glassdoor Job Search API via RapidAPI (100 req/mo free)."""

    def __init__(self, api_key: str, timeout: float = 10.0):
        """
        Args:
            api_key: RapidAPI key (set RAPIDAPI_KEY in env).
        """
        self.api_key = api_key
        self.timeout = timeout
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": RAPIDAPI_HOST,
        }

    async def search_jobs(
        self,
        query: str,
        location: Optional[str] = None,
        page: int = 1,
    ) -> dict:
        """
        Search jobs on Glassdoor.

        Args:
            query: job title or keywords.
            location: city or country.
            page: results page.

        Returns:
            Raw JSON response from RapidAPI.
        """
        params: dict = {"query": query, "page": page}
        if location:
            params["location"] = location

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(BASE_URL, params=params, headers=self.headers)
            resp.raise_for_status()
            return resp.json()
