import uuid
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel
from app.models.campaign import CampaignStatus


class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = None
    status: CampaignStatus = CampaignStatus.draft


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = None
    status: Optional[CampaignStatus] = None


class CampaignRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = None
    status: CampaignStatus
    created_at: datetime

    model_config = {"from_attributes": True}
