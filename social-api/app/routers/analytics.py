from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.analytics import Analytics
from app.models.social_account import SocialAccount
from app.schemas.analytics import AnalyticsOut
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=list[AnalyticsOut])
async def get_analytics(
    account_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return analytics rows for the current user's accounts."""
    # Get all account ids belonging to the user
    acct_result = await db.execute(
        select(SocialAccount.id).where(SocialAccount.user_id == current_user.id)
    )
    user_account_ids = [row[0] for row in acct_result.all()]

    query = select(Analytics).where(Analytics.social_account_id.in_(user_account_ids))
    if account_id and account_id in user_account_ids:
        query = query.where(Analytics.social_account_id == account_id)

    result = await db.execute(query.order_by(Analytics.date.desc()).limit(500))
    return result.scalars().all()
