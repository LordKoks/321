import uuid
import enum
from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, Enum as SAEnum, func
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.database import Base


class PostStatus(str, enum.Enum):
    draft = "draft"
    scheduled = "scheduled"
    published = "published"
    failed = "failed"


class PostTargetStatus(str, enum.Enum):
    pending = "pending"
    published = "published"
    failed = "failed"


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    media_urls: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True, default=list)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[PostStatus] = mapped_column(
        SAEnum(PostStatus), nullable=False, default=PostStatus.draft
    )
    platform_post_ids: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="posts")  # noqa: F821
    targets: Mapped[list["PostTarget"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )


class PostTarget(Base):
    __tablename__ = "post_targets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    social_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("social_accounts.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[PostTargetStatus] = mapped_column(
        SAEnum(PostTargetStatus), nullable=False, default=PostTargetStatus.pending
    )
    error_message: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    post: Mapped["Post"] = relationship(back_populates="targets")
    social_account: Mapped["SocialAccount"] = relationship(back_populates="post_targets")  # noqa: F821
    analytics: Mapped[list["Analytics"]] = relationship(  # noqa: F821
        back_populates="post_target", cascade="all, delete-orphan"
    )
