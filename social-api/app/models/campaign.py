import uuid
import enum
from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Text, DateTime, Date, ForeignKey, Numeric, Enum as SAEnum, func
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.database import Base


class CampaignStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    completed = "completed"
    draft = "draft"


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    budget: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[CampaignStatus] = mapped_column(
        SAEnum(CampaignStatus), nullable=False, default=CampaignStatus.draft
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="campaigns")  # noqa: F821
