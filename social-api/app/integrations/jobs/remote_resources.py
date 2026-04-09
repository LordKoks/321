"""
Remote Work Resources API — free, no API key required.
Source: https://github.com/nata-ferguson/remote-work-resources-api
Returns a list of job boards and platforms (not individual vacancies).
"""

from typing import Optional
import httpx

BASE_URL = "https://nf-remote-work-resources-api.vercel.app/api/remoteWorkResource"


class RemoteResourcesClient:
    """Client for the Remote Work Resources API (no key required)."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    async def get_resources(
        self,
        category: Optional[str] = None,
        region: Optional[str] = None,
    ) -> list[dict]:
        """
        Fetch remote work resource listings.

        Args:
            category: e.g. "Job Board", "Freelance", "Community".
            region: e.g. "Global", "USA", "Europe".

        Returns:
            List of resource dicts with name, url, category, region.
        """
        params: dict = {}
        if category:
            params["category"] = category
        if region:
            params["region"] = region

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            # API may return a list or a dict with a data key
            if isinstance(data, list):
                return data
            return data.get("data", data)
