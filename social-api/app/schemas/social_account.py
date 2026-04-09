import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel
from app.models.social_account import Platform


class SocialAccountRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    platform: Platform
    account_id: str
    account_name: Optional[str] = None
    token_type: Optional[str] = None
    expires_at: Optional[datetime] = None
    extra_data: Optional[Any] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SocialAccountCreate(BaseModel):
    platform: Platform
    account_id: str
    account_name: Optional[str] = None
    token: Optional[str] = None
    token_type: Optional[str] = "bearer"
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    extra_data: Optional[Any] = None


class OAuthCallbackParams(BaseModel):
    code: str
    state: Optional[str] = None
