from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.post import Post, PostTarget, PostStatus
from app.models.social_account import SocialAccount
from app.schemas.post import PostCreate, PostOut, PostUpdate
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=list[PostOut])
async def list_posts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Post).where(Post.user_id == current_user.id).order_by(Post.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(
    data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    post = Post(
        user_id=current_user.id,
        content=data.content,
        media_urls=data.media_urls or [],
        scheduled_at=data.scheduled_at,
        status=PostStatus.scheduled if data.scheduled_at else PostStatus.draft,
    )
    db.add(post)
    await db.flush()

    for account_id in data.target_account_ids:
        # verify ownership
        res = await db.execute(
            select(SocialAccount).where(
                SocialAccount.id == account_id,
                SocialAccount.user_id == current_user.id,
            )
        )
        if not res.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
        target = PostTarget(post_id=post.id, social_account_id=account_id, status=PostStatus.scheduled)
        db.add(target)

    await db.commit()
    await db.refresh(post)
    return post


@router.get("/{post_id}", response_model=PostOut)
async def get_post(
    post_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == current_user.id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.patch("/{post_id}", response_model=PostOut)
async def update_post(
    post_id: UUID,
    data: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == current_user.id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(post, field, value)
    post.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(post)
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.user_id == current_user.id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    await db.delete(post)
    await db.commit()
