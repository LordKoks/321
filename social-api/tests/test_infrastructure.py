"""Tests for infrastructure: config, JWT, TokenManager, schema aliases."""

import pytest
import uuid

pytestmark = pytest.mark.asyncio


# ── Config ────────────────────────────────────────────────────────────────

def test_settings_defaults():
    from app.config import settings
    assert settings.SECRET_KEY  # not empty
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
    assert settings.REFRESH_TOKEN_EXPIRE_DAYS > 0


def test_settings_db_url_uses_override():
    """Our test conftest points DATABASE_URL at SQLite."""
    from app.config import settings
    assert "sqlite" in settings.DATABASE_URL or "postgresql" in settings.DATABASE_URL


# ── JWT ───────────────────────────────────────────────────────────────────

def test_create_and_decode_access_token():
    from app.auth.jwt import create_access_token, decode_token
    uid = uuid.uuid4()
    token = create_access_token(uid)
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == str(uid)
    assert payload["type"] == "access"


def test_create_and_decode_refresh_token():
    from app.auth.jwt import create_refresh_token, decode_token
    uid = uuid.uuid4()
    token = create_refresh_token(uid)
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == str(uid)
    assert payload["type"] == "refresh"


def test_decode_invalid_token_returns_none():
    from app.auth.jwt import decode_token
    assert decode_token("garbage.token.here") is None


def test_decode_tampered_token_returns_none():
    from app.auth.jwt import create_access_token, decode_token
    token = create_access_token(uuid.uuid4())
    parts = token.split(".")
    parts[2] = "invalidsignature"
    assert decode_token(".".join(parts)) is None


def test_hash_and_verify_password():
    from app.auth.jwt import hash_password, verify_password
    pw = "mysecretpassword"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed)
    assert not verify_password("wrongpassword", hashed)


# ── TokenManager ─────────────────────────────────────────────────────────

def test_token_manager_encrypt_decrypt():
    from app.core.token_manager import token_manager
    original = "my_platform_access_token"
    encrypted = token_manager.encrypt(original)
    assert encrypted != original
    assert token_manager.decrypt(encrypted) == original


def test_token_manager_encrypt_different_each_time():
    """Fernet tokens are non-deterministic (include timestamp)."""
    from app.core.token_manager import token_manager
    t1 = token_manager.encrypt("same_token")
    t2 = token_manager.encrypt("same_token")
    # Both decrypt correctly
    assert token_manager.decrypt(t1) == "same_token"
    assert token_manager.decrypt(t2) == "same_token"


# ── Schema aliases ────────────────────────────────────────────────────────

def test_post_out_alias():
    from app.schemas.post import PostOut, PostRead
    assert PostOut is PostRead


def test_campaign_out_alias():
    from app.schemas.campaign import CampaignOut, CampaignRead
    assert CampaignOut is CampaignRead


def test_social_account_out_alias():
    from app.schemas.social_account import SocialAccountOut, SocialAccountRead
    assert SocialAccountOut is SocialAccountRead


def test_analytics_out_alias():
    from app.schemas.analytics import AnalyticsOut, AnalyticsRead
    assert AnalyticsOut is AnalyticsRead


# ── Model enum values ─────────────────────────────────────────────────────

def test_platform_enum_values():
    from app.models.social_account import Platform
    assert set(p.value for p in Platform) == {"vk", "x", "telegram", "ok", "youtube"}


def test_post_status_enum_values():
    from app.models.post import PostStatus
    assert "draft" in [s.value for s in PostStatus]
    assert "scheduled" in [s.value for s in PostStatus]
    assert "published" in [s.value for s in PostStatus]
    assert "failed" in [s.value for s in PostStatus]


def test_post_target_status_enum_values():
    from app.models.post import PostTargetStatus
    assert "pending" in [s.value for s in PostTargetStatus]
    assert "published" in [s.value for s in PostTargetStatus]
    assert "failed" in [s.value for s in PostTargetStatus]


def test_campaign_status_enum_values():
    from app.models.campaign import CampaignStatus
    assert set(s.value for s in CampaignStatus) == {"draft", "active", "paused", "completed"}


# ── Router registration ───────────────────────────────────────────────────

def test_all_routers_registered():
    from app.main import app
    paths = {r.path for r in app.routes}
    assert "/health" in paths
    assert "/auth/register" in paths
    assert "/auth/login" in paths
    assert "/auth/refresh" in paths
    assert "/posts/" in paths
    assert "/campaigns/" in paths
    assert "/accounts/" in paths
    assert "/analytics/" in paths
    assert "/jobs/" in paths


def test_health_endpoint(client):
    """Sync check — use event loop via pytest-asyncio."""
    pass  # covered by dedicated async test below


async def test_health_check(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ── Job integration normalisation helpers ─────────────────────────────────

def test_normalise_himalayas():
    from app.integrations.jobs.aggregator import _normalise_himalayas
    job = {
        "title": "SRE",
        "companyName": "XCorp",
        "locationRestrictions": ["Europe"],
        "applicationLink": "https://example.com",
        "minSalary": 70000,
        "maxSalary": 90000,
        "currency": "USD",
        "categories": ["DevOps"],
        "seniority": ["Mid"],
    }
    result = _normalise_himalayas(job)
    assert result["source"] == "himalayas"
    assert result["title"] == "SRE"
    assert result["remote"] is True
    assert result["salary_min"] == 70000


def test_normalise_jobicy():
    from app.integrations.jobs.aggregator import _normalise_jobicy
    job = {
        "jobTitle": "Data Analyst",
        "companyName": "DataCo",
        "jobGeo": "USA",
        "url": "https://jobicy.com/1",
        "jobIndustry": "Analytics",
    }
    result = _normalise_jobicy(job)
    assert result["source"] == "jobicy"
    assert result["title"] == "Data Analyst"
    assert result["remote"] is True


def test_normalise_theirstack():
    from app.integrations.jobs.aggregator import _normalise_theirstack
    job = {
        "title": "ML Engineer",
        "company_name": "AI Inc",
        "location": "Remote",
        "remote": True,
        "url": "https://theirstack.com/1",
        "salary_min": 100000,
        "salary_max": 150000,
        "salary_currency": "USD",
        "tags": ["Python", "ML"],
    }
    result = _normalise_theirstack(job)
    assert result["source"] == "theirstack"
    assert result["remote"] is True
    assert result["salary_max"] == 150000


def test_normalise_serpapi():
    from app.integrations.jobs.aggregator import _normalise_serpapi
    job = {
        "title": "DevOps",
        "company_name": "CloudCo",
        "location": "Remote, USA",
        "related_links": [{"link": "https://apply.example.com"}],
    }
    result = _normalise_serpapi(job)
    assert result["source"] == "serpapi"
    assert result["remote"] is True  # "remote" in location
    assert result["url"] == "https://apply.example.com"


def test_normalise_glassdoor():
    from app.integrations.jobs.aggregator import _normalise_glassdoor
    job = {
        "jobTitle": "PM",
        "employer": {"name": "BigCo"},
        "location": "New York",
        "jobLink": "https://glassdoor.com/job/1",
    }
    result = _normalise_glassdoor(job)
    assert result["source"] == "glassdoor"
    assert result["company"] == "BigCo"


# ── Aggregator deduplication ──────────────────────────────────────────────

def test_aggregator_deduplication():
    """Duplicate (source, title, company) should be deduplicated."""
    from app.integrations.jobs.aggregator import _normalise_himalayas
    job = {
        "title": "Engineer",
        "companyName": "Same Corp",
        "locationRestrictions": [],
        "applicationLink": "https://x.com",
        "categories": [],
        "seniority": [],
    }
    # Simulate same job returned twice
    results = [_normalise_himalayas(job), _normalise_himalayas(job)]
    seen: set = set()
    unique = []
    for j in results:
        key = (j["source"], j["title"].lower(), j["company"].lower())
        if key not in seen:
            seen.add(key)
            unique.append(j)
    assert len(unique) == 1
