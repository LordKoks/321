"""
Job Aggregator — unified interface across all job sources.
Normalises results to a common JobListing schema and merges them.
"""

from typing import Optional
from app.integrations.jobs.himalayas import HimalayasClient
from app.integrations.jobs.jobicy import JobicyClient
from app.integrations.jobs.glassdoor import GlassdoorClient
from app.integrations.jobs.theirstack import TheirStackClient
from app.integrations.jobs.serpapi import SerpApiClient


def _normalise_himalayas(job: dict) -> dict:
    return {
        "source": "himalayas",
        "title": job.get("title", ""),
        "company": job.get("companyName", ""),
        "location": job.get("locationRestrictions", []),
        "remote": True,
        "url": job.get("applicationLink", ""),
        "salary_min": job.get("minSalary"),
        "salary_max": job.get("maxSalary"),
        "currency": job.get("currency"),
        "categories": job.get("categories", []),
        "seniority": job.get("seniority", []),
        "raw": job,
    }


def _normalise_jobicy(job: dict) -> dict:
    return {
        "source": "jobicy",
        "title": job.get("jobTitle", ""),
        "company": job.get("companyName", ""),
        "location": [job.get("jobGeo", "")],
        "remote": True,
        "url": job.get("url", ""),
        "salary_min": None,
        "salary_max": None,
        "currency": None,
        "categories": [job.get("jobIndustry", "")],
        "seniority": [],
        "raw": job,
    }


def _normalise_glassdoor(job: dict) -> dict:
    return {
        "source": "glassdoor",
        "title": job.get("jobTitle", ""),
        "company": job.get("employer", {}).get("name", ""),
        "location": [job.get("location", "")],
        "remote": False,
        "url": job.get("jobLink", ""),
        "salary_min": None,
        "salary_max": None,
        "currency": None,
        "categories": [],
        "seniority": [],
        "raw": job,
    }


def _normalise_theirstack(job: dict) -> dict:
    return {
        "source": "theirstack",
        "title": job.get("title", ""),
        "company": job.get("company_name", ""),
        "location": [job.get("location", "")],
        "remote": job.get("remote", False),
        "url": job.get("url", ""),
        "salary_min": job.get("salary_min"),
        "salary_max": job.get("salary_max"),
        "currency": job.get("salary_currency"),
        "categories": job.get("tags", []),
        "seniority": [],
        "raw": job,
    }


def _normalise_serpapi(job: dict) -> dict:
    return {
        "source": "serpapi",
        "title": job.get("title", ""),
        "company": job.get("company_name", ""),
        "location": [job.get("location", "")],
        "remote": "remote" in job.get("location", "").lower(),
        "url": job.get("related_links", [{}])[0].get("link", ""),
        "salary_min": None,
        "salary_max": None,
        "currency": None,
        "categories": job.get("detected_extensions", {}).get("category", []),
        "seniority": [],
        "raw": job,
    }


class JobAggregator:
    """
    Aggregates job listings from multiple sources into a unified format.
    Only sources with configured credentials are queried.
    """

    def __init__(
        self,
        rapidapi_key: Optional[str] = None,
        theirstack_api_key: Optional[str] = None,
        serpapi_key: Optional[str] = None,
    ):
        self.himalayas = HimalayasClient()
        self.jobicy = JobicyClient()
        self.glassdoor = GlassdoorClient(rapidapi_key) if rapidapi_key else None
        self.theirstack = TheirStackClient(theirstack_api_key) if theirstack_api_key else None
        self.serpapi = SerpApiClient(serpapi_key) if serpapi_key else None

    async def search(
        self,
        query: str,
        location: Optional[str] = None,
        category: Optional[str] = None,
        remote_only: bool = True,
        limit_per_source: int = 20,
    ) -> list[dict]:
        """
        Search jobs across all configured sources and return normalised results.

        Args:
            query: job title / keywords.
            location: optional location string.
            category: optional job category (used for Himalayas / Jobicy).
            remote_only: only return remote positions.
            limit_per_source: max jobs to fetch from each source.

        Returns:
            Flat list of normalised job dicts, deduplicated by title+company.
        """
        results: list[dict] = []

        # --- Himalayas (always available) ---
        try:
            data = await self.himalayas.get_jobs(
                limit=min(limit_per_source, 20),
                query=query,
                category=category,
            )
            for job in data.get("jobs", []):
                results.append(_normalise_himalayas(job))
        except Exception:
            pass

        # --- Jobicy (always available) ---
        try:
            data = await self.jobicy.get_jobs(count=limit_per_source, tag=query, geo=location)
            for job in data.get("jobs", []):
                results.append(_normalise_jobicy(job))
        except Exception:
            pass

        # --- Glassdoor (RapidAPI key required) ---
        if self.glassdoor:
            try:
                data = await self.glassdoor.search_jobs(query=query, location=location)
                for job in data.get("jobs", data.get("results", [])):
                    results.append(_normalise_glassdoor(job))
            except Exception:
                pass

        # --- TheirStack (API key required) ---
        if self.theirstack:
            try:
                data = await self.theirstack.search_jobs(
                    query=query,
                    location=location,
                    remote=remote_only,
                    limit=limit_per_source,
                )
                for job in data.get("data", []):
                    results.append(_normalise_theirstack(job))
            except Exception:
                pass

        # --- SerpApi (API key required) ---
        if self.serpapi:
            try:
                data = await self.serpapi.search_jobs(query=query, location=location)
                for job in data.get("jobs_results", []):
                    results.append(_normalise_serpapi(job))
            except Exception:
                pass

        # Deduplicate by (source, title, company)
        seen: set[tuple] = set()
        unique: list[dict] = []
        for job in results:
            key = (job["source"], job["title"].lower(), job["company"].lower())
            if key not in seen:
                seen.add(key)
                unique.append(job)

        if remote_only:
            unique = [j for j in unique if j.get("remote", False)]

        return unique
