"""
Himalayas Remote Jobs API — free, no API key required.
Docs: https://himalayas.app/docs/remote-jobs-api
Attribution: links to himalayas.app are required when displaying data.
"""

from typing import Optional
import httpx

BASE_URL = "https://himalayas.app/jobs/api"


class HimalayasClient:
    """Client for the Himalayas Remote Jobs API (no key, 20 jobs/request)."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    async def get_jobs(
        self,
        limit: int = 20,
        offset: int = 0,
        query: Optional[str] = None,
        category: Optional[str] = None,
    ) -> dict:
        """
        Fetch remote jobs from Himalayas.

        Args:
            limit: number of jobs to return (max 20 per request).
            offset: pagination offset.
            query: optional search term.
            category: optional category filter, e.g. "Engineering", "Design".

        Returns:
            Raw JSON response dict with keys: jobs (list), total, hasMore.
        """
        params: dict = {"limit": limit, "offset": offset}
        if query:
            params["q"] = query
        if category:
            params["category"] = category

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = client.get(BASE_URL, params=params)
            # httpx async context requires await — use sync for simplicity in tasks
            # but we expose an async interface consistent with the rest of the codebase
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(BASE_URL, params=params)
            resp.raise_for_status()
            return resp.json()

    async def get_all_pages(
        self,
        max_jobs: int = 100,
        query: Optional[str] = None,
        category: Optional[str] = None,
    ) -> list[dict]:
        """Fetch multiple pages and return a flat list of job dicts."""
        jobs: list[dict] = []
        offset = 0
        page_size = 20
        while len(jobs) < max_jobs:
            data = await self.get_jobs(
                limit=min(page_size, max_jobs - len(jobs)),
                offset=offset,
                query=query,
                category=category,
            )
            page = data.get("jobs", [])
            if not page:
                break
            jobs.extend(page)
            if not data.get("hasMore", False):
                break
            offset += page_size
        return jobs
