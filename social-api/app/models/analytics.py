import uuid
from datetime import datetime, date
from typing import Optional
from sqlalchemy import Date, DateTime, ForeignKey, Integer, BigInteger, func
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.database import Base


class Analytics(Base):
    __tablename__ = "analytics"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    social_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("social_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    post_target_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("post_targets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    views: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    shares: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reach: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    social_account: Mapped["SocialAccount"] = relationship(back_populates="analytics")  # noqa: F821
    post_target: Mapped[Optional["PostTarget"]] = relationship(back_populates="analytics")  # noqa: F821
