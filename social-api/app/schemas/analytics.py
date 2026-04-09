import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class AnalyticsRead(BaseModel):
    id: uuid.UUID
    social_account_id: uuid.UUID
    post_target_id: Optional[uuid.UUID] = None
    date: date
    likes: int
    views: int
    shares: int
    comments: int
    reach: int
    created_at: datetime

    model_config = {"from_attributes": True}


AnalyticsOut = AnalyticsRead


class AnalyticsSummary(BaseModel):
    total_likes: int
    total_views: int
    total_shares: int
    total_comments: int
    total_reach: int
    records: list[AnalyticsRead]
