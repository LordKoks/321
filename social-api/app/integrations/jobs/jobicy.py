"""
Jobicy Public API — free, no API key required.
Docs: https://jobicy.com/docs
Specialises in remote IT, marketing, and design positions.
"""

from typing import Optional
import httpx

BASE_URL = "https://jobicy.com/api/v2/remote-jobs"


class JobicyClient:
    """Client for the Jobicy Remote Jobs API (no key, 20 jobs/request)."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    async def get_jobs(
        self,
        count: int = 20,
        industry: Optional[str] = None,
        tag: Optional[str] = None,
        geo: Optional[str] = None,
    ) -> dict:
        """
        Fetch remote jobs from Jobicy.

        Args:
            count: number of jobs (1-50).
            industry: e.g. "software-development", "design", "marketing".
            tag: skill tag filter, e.g. "python", "react".
            geo: region filter, e.g. "usa", "europe", "worldwide".

        Returns:
            Raw JSON response dict with keys: jobs (list), query_count, etc.
        """
        params: dict = {"count": min(count, 50)}
        if industry:
            params["industry"] = industry
        if tag:
            params["tag"] = tag
        if geo:
            params["geo"] = geo

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(BASE_URL, params=params)
            resp.raise_for_status()
            return resp.json()
