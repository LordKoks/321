import uuid
import enum
from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, DateTime, ForeignKey, JSON, Enum as SAEnum, func
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.database import Base


class Platform(str, enum.Enum):
    vk = "vk"
    x = "x"
    telegram = "telegram"
    ok = "ok"
    youtube = "youtube"


class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[Platform] = mapped_column(SAEnum(Platform), nullable=False)
    account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    account_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    encrypted_token: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    token_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, default="bearer")
    refresh_token_encrypted: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    extra_data: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="social_accounts")  # noqa: F821
    post_targets: Mapped[list["PostTarget"]] = relationship(  # noqa: F821
        back_populates="social_account", cascade="all, delete-orphan"
    )
    analytics: Mapped[list["Analytics"]] = relationship(  # noqa: F821
        back_populates="social_account", cascade="all, delete-orphan"
    )
