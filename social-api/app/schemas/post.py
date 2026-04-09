import uuid
from datetime import datetime
from typing import Optional, Any, List
from pydantic import BaseModel
from app.models.post import PostStatus, PostTargetStatus


class PostTargetRead(BaseModel):
    id: uuid.UUID
    post_id: uuid.UUID
    social_account_id: uuid.UUID
    status: PostTargetStatus
    error_message: Optional[str] = None
    published_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PostCreate(BaseModel):
    content: str
    media_urls: Optional[List[str]] = None
    scheduled_at: Optional[datetime] = None
    target_account_ids: Optional[List[uuid.UUID]] = None


class PostUpdate(BaseModel):
    content: Optional[str] = None
    media_urls: Optional[List[str]] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[PostStatus] = None


class PostRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    content: str
    media_urls: Optional[Any] = None
    scheduled_at: Optional[datetime] = None
    status: PostStatus
    platform_post_ids: Optional[Any] = None
    created_at: datetime
    updated_at: datetime
    targets: List[PostTargetRead] = []

    model_config = {"from_attributes": True}
