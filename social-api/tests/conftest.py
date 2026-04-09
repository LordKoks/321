"""
Shared fixtures for all tests.

Uses an in-memory SQLite database (via aiosqlite) so no PostgreSQL is needed.
The app's DATABASE_URL is overridden before any imports touch the engine.
"""

import os
import sys
import pytest
import pytest_asyncio

# ── point at the app package ───────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Must set env vars BEFORE importing app modules that read settings at import-time
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_social.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-xxxxxxxx")

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event

# ── create a fresh in-memory engine per test session ──────────────────────
TEST_DB_URL = "sqlite+aiosqlite:///./test_social_api.db"

engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    """Create all tables once for the test session."""
    from app.database import Base
    # Import all models so metadata is populated
    import app.models.user  # noqa
    import app.models.social_account  # noqa
    import app.models.post  # noqa
    import app.models.campaign  # noqa
    import app.models.analytics  # noqa

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    """Truncate all tables between tests."""
    yield
    async with engine.begin() as conn:
        from sqlalchemy import text
        # Delete in FK-safe order
        for table in [
            "analytics", "post_targets", "posts",
            "social_accounts", "campaigns", "users",
        ]:
            await conn.execute(text(f"DELETE FROM {table}"))


@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    """
    Returns an httpx AsyncClient configured to talk to the FastAPI app
    with the DB overridden to SQLite.
    """
    from app.main import app
    from app.database import get_db

    async def override_get_db():
        async with TestSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


# ── helper: register + login, return auth headers ─────────────────────────

async def register_and_login(client: AsyncClient, email: str, password: str) -> dict:
    """Register a user, log in, and return bearer headers."""
    reg = await client.post("/auth/register", json={"email": email, "password": password})
    assert reg.status_code == 201, reg.text
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
