# Import all models so that Base.metadata includes all tables for Alembic
from app.database import Base  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.social_account import SocialAccount  # noqa: F401
from app.models.post import Post, PostTarget  # noqa: F401
from app.models.campaign import Campaign  # noqa: F401
from app.models.analytics import Analytics  # noqa: F401

__all__ = ["Base", "User", "SocialAccount", "Post", "PostTarget", "Campaign", "Analytics"]
