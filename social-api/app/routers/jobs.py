"""
Jobs router — exposes job listings from multiple free/freemium APIs.
All endpoints are public (no auth required) to allow frontend demos.
"""

from typing import Optional
from fastapi import APIRouter, Query, Depends
from app.config import get_settings
from app.integrations.jobs.himalayas import HimalayasClient
from app.integrations.jobs.jobicy import JobicyClient
from app.integrations.jobs.remote_resources import RemoteResourcesClient
from app.integrations.jobs.aggregator import JobAggregator

router = APIRouter()


def _get_aggregator():
    s = get_settings()
    return JobAggregator(
        rapidapi_key=s.RAPIDAPI_KEY,
        theirstack_api_key=s.THEIRSTACK_API_KEY,
        serpapi_key=s.SERPAPI_KEY,
    )


@router.get("/")
async def search_jobs(
    q: str = Query(..., description="Job title or keywords"),
    location: Optional[str] = Query(None, description="Location filter"),
    category: Optional[str] = Query(None, description="Category filter (e.g. Engineering)"),
    remote_only: bool = Query(True, description="Only return remote positions"),
    limit: int = Query(20, ge=1, le=100),
    aggregator: JobAggregator = Depends(_get_aggregator),
):
    """Aggregate job listings from all configured sources."""
    jobs = await aggregator.search(
        query=q,
        location=location,
        category=category,
        remote_only=remote_only,
        limit_per_source=limit,
    )
    return {"count": len(jobs), "jobs": jobs}


@router.get("/himalayas")
async def himalayas_jobs(
    q: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=20),
    offset: int = Query(0, ge=0),
):
    """Direct access to Himalayas Remote Jobs API (free, no key)."""
    client = HimalayasClient()
    return await client.get_jobs(limit=limit, offset=offset, query=q, category=category)


@router.get("/jobicy")
async def jobicy_jobs(
    tag: Optional[str] = Query(None, description="Skill tag e.g. python, react"),
    industry: Optional[str] = Query(None, description="e.g. software-development"),
    geo: Optional[str] = Query(None, description="e.g. usa, europe, worldwide"),
    count: int = Query(20, ge=1, le=50),
):
    """Direct access to Jobicy Remote Jobs API (free, no key)."""
    client = JobicyClient()
    return await client.get_jobs(count=count, industry=industry, tag=tag, geo=geo)


@router.get("/resources")
async def remote_resources(
    category: Optional[str] = Query(None, description="e.g. Job Board, Freelance"),
    region: Optional[str] = Query(None, description="e.g. Global, USA, Europe"),
):
    """Remote work resources (job boards, communities) — free, no key."""
    client = RemoteResourcesClient()
    data = await client.get_resources(category=category, region=region)
    return {"count": len(data), "resources": data}
