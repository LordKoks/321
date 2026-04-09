"""Tests for /jobs endpoints (mock HTTP, no external calls)."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

MOCK_HIMALAYAS_RESPONSE = {
    "jobs": [
        {
            "title": "Backend Engineer",
            "companyName": "Acme Corp",
            "locationRestrictions": ["Worldwide"],
            "applicationLink": "https://himalayas.app/jobs/1",
            "minSalary": 80000,
            "maxSalary": 120000,
            "currency": "USD",
            "categories": ["Engineering"],
            "seniority": ["Senior"],
        }
    ]
}

MOCK_JOBICY_RESPONSE = {
    "jobs": [
        {
            "jobTitle": "Frontend Dev",
            "companyName": "Beta Ltd",
            "jobGeo": "USA",
            "url": "https://jobicy.com/jobs/2",
            "jobIndustry": "Software",
        }
    ]
}


async def test_himalayas_endpoint_mocked(client: AsyncClient):
    with patch(
        "app.integrations.jobs.himalayas.HimalayasClient.get_jobs",
        new_callable=AsyncMock,
        return_value=MOCK_HIMALAYAS_RESPONSE,
    ):
        r = await client.get("/jobs/himalayas?q=engineer&limit=5")
    assert r.status_code == 200
    body = r.json()
    assert "jobs" in body
    assert len(body["jobs"]) == 1
    assert body["jobs"][0]["title"] == "Backend Engineer"


async def test_jobicy_endpoint_mocked(client: AsyncClient):
    with patch(
        "app.integrations.jobs.jobicy.JobicyClient.get_jobs",
        new_callable=AsyncMock,
        return_value=MOCK_JOBICY_RESPONSE,
    ):
        r = await client.get("/jobs/jobicy?tag=python&count=10")
    assert r.status_code == 200
    body = r.json()
    assert "jobs" in body
    assert body["jobs"][0]["jobTitle"] == "Frontend Dev"


async def test_jobs_aggregator_endpoint(client: AsyncClient):
    """Aggregator should return normalised results from both Himalayas and Jobicy."""
    with (
        patch(
            "app.integrations.jobs.himalayas.HimalayasClient.get_jobs",
            new_callable=AsyncMock,
            return_value=MOCK_HIMALAYAS_RESPONSE,
        ),
        patch(
            "app.integrations.jobs.jobicy.JobicyClient.get_jobs",
            new_callable=AsyncMock,
            return_value=MOCK_JOBICY_RESPONSE,
        ),
    ):
        r = await client.get("/jobs/?q=engineer&remote_only=false")
    assert r.status_code == 200
    body = r.json()
    assert "count" in body
    assert "jobs" in body
    assert body["count"] == len(body["jobs"])
    sources = {j["source"] for j in body["jobs"]}
    assert "himalayas" in sources
    assert "jobicy" in sources


async def test_jobs_aggregator_remote_filter(client: AsyncClient):
    """remote_only=true should filter out non-remote jobs."""
    with (
        patch(
            "app.integrations.jobs.himalayas.HimalayasClient.get_jobs",
            new_callable=AsyncMock,
            return_value=MOCK_HIMALAYAS_RESPONSE,  # marked remote=True in normaliser
        ),
        patch(
            "app.integrations.jobs.jobicy.JobicyClient.get_jobs",
            new_callable=AsyncMock,
            return_value=MOCK_JOBICY_RESPONSE,  # marked remote=True in normaliser
        ),
    ):
        r = await client.get("/jobs/?q=dev&remote_only=true")
    assert r.status_code == 200
    for job in r.json()["jobs"]:
        assert job["remote"] is True


async def test_resources_endpoint_mocked(client: AsyncClient):
    mock_resources = [
        {"name": "Remote OK", "url": "https://remoteok.com", "category": "Job Board", "region": "Global"}
    ]
    with patch(
        "app.integrations.jobs.remote_resources.RemoteResourcesClient.get_resources",
        new_callable=AsyncMock,
        return_value=mock_resources,
    ):
        r = await client.get("/jobs/resources")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 1
    assert body["resources"][0]["name"] == "Remote OK"


async def test_jobs_aggregator_handles_source_failure(client: AsyncClient):
    """If one source raises an exception, aggregator still returns results from others."""
    import httpx

    with (
        patch(
            "app.integrations.jobs.himalayas.HimalayasClient.get_jobs",
            new_callable=AsyncMock,
            side_effect=httpx.HTTPError("network error"),
        ),
        patch(
            "app.integrations.jobs.jobicy.JobicyClient.get_jobs",
            new_callable=AsyncMock,
            return_value=MOCK_JOBICY_RESPONSE,
        ),
    ):
        r = await client.get("/jobs/?q=test&remote_only=false")
    assert r.status_code == 200
    sources = {j["source"] for j in r.json()["jobs"]}
    assert "jobicy" in sources
    assert "himalayas" not in sources


async def test_jobs_require_q_param(client: AsyncClient):
    r = await client.get("/jobs/")
    assert r.status_code == 422  # missing required 'q'
