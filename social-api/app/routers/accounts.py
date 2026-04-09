from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.social_account import SocialAccount, Platform
from app.schemas.social_account import SocialAccountCreate, SocialAccountOut
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.core.token_manager import token_manager
from app.integrations.vk.oauth import VKOAuth
from app.integrations.x.oauth import XOAuth
from app.integrations.ok.oauth import OKOAuth
from app.integrations.youtube.oauth import YouTubeOAuth
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/", response_model=list[SocialAccountOut])
async def list_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SocialAccount).where(SocialAccount.user_id == current_user.id)
    )
    return result.scalars().all()


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SocialAccount).where(
            SocialAccount.id == account_id,
            SocialAccount.user_id == current_user.id,
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    await db.delete(account)
    await db.commit()


# ── VK ──────────────────────────────────────────────────────────────────────

@router.get("/vk/connect")
async def vk_connect(current_user: User = Depends(get_current_user)):
    oauth = VKOAuth(settings.VK_APP_ID, settings.VK_APP_SECRET, settings.VK_REDIRECT_URI)
    url = oauth.get_auth_url(state=str(current_user.id))
    return {"url": url}


@router.get("/vk/callback")
async def vk_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    oauth = VKOAuth(settings.VK_APP_ID, settings.VK_APP_SECRET, settings.VK_REDIRECT_URI)
    token_data = await oauth.exchange_code(code)
    encrypted = token_manager.encrypt(token_data["access_token"])
    account = SocialAccount(
        user_id=UUID(state),
        platform=Platform.vk,
        account_id=str(token_data.get("user_id", "")),
        encrypted_token=encrypted,
        token_type="bearer",
        extra_data=token_data,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return {"id": account.id, "platform": "vk"}


# ── X ───────────────────────────────────────────────────────────────────────

@router.get("/x/connect")
async def x_connect(current_user: User = Depends(get_current_user)):
    oauth = XOAuth(settings.X_CLIENT_ID, settings.X_CLIENT_SECRET, settings.X_REDIRECT_URI)
    url, code_verifier = oauth.get_auth_url(state=str(current_user.id))
    return {"url": url, "code_verifier": code_verifier}


@router.get("/x/callback")
async def x_callback(
    code: str,
    state: str,
    code_verifier: str,
    db: AsyncSession = Depends(get_db),
):
    oauth = XOAuth(settings.X_CLIENT_ID, settings.X_CLIENT_SECRET, settings.X_REDIRECT_URI)
    token_data = await oauth.exchange_code(code, code_verifier)
    encrypted = token_manager.encrypt(token_data["access_token"])
    refresh_encrypted = token_manager.encrypt(token_data.get("refresh_token", ""))
    account = SocialAccount(
        user_id=UUID(state),
        platform=Platform.x,
        account_id=token_data.get("sub", ""),
        encrypted_token=encrypted,
        refresh_token_encrypted=refresh_encrypted,
        token_type="bearer",
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return {"id": account.id, "platform": "x"}


# ── OK ───────────────────────────────────────────────────────────────────────

@router.get("/ok/connect")
async def ok_connect(current_user: User = Depends(get_current_user)):
    oauth = OKOAuth(settings.OK_APP_ID, settings.OK_APP_SECRET, settings.OK_REDIRECT_URI)
    url = oauth.get_auth_url(state=str(current_user.id))
    return {"url": url}


@router.get("/ok/callback")
async def ok_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    oauth = OKOAuth(settings.OK_APP_ID, settings.OK_APP_SECRET, settings.OK_REDIRECT_URI)
    token_data = await oauth.exchange_code(code)
    encrypted = token_manager.encrypt(token_data["access_token"])
    account = SocialAccount(
        user_id=UUID(state),
        platform=Platform.ok,
        account_id=str(token_data.get("uid", "")),
        encrypted_token=encrypted,
        token_type="bearer",
        extra_data=token_data,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return {"id": account.id, "platform": "ok"}


# ── YouTube ──────────────────────────────────────────────────────────────────

@router.get("/youtube/connect")
async def youtube_connect(current_user: User = Depends(get_current_user)):
    oauth = YouTubeOAuth(
        settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET, settings.GOOGLE_REDIRECT_URI
    )
    url = oauth.get_auth_url(state=str(current_user.id))
    return {"url": url}


@router.get("/youtube/callback")
async def youtube_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    oauth = YouTubeOAuth(
        settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET, settings.GOOGLE_REDIRECT_URI
    )
    token_data = await oauth.exchange_code(code)
    encrypted = token_manager.encrypt(token_data["access_token"])
    refresh_encrypted = token_manager.encrypt(token_data.get("refresh_token", ""))
    account = SocialAccount(
        user_id=UUID(state),
        platform=Platform.youtube,
        account_id=token_data.get("sub", ""),
        encrypted_token=encrypted,
        refresh_token_encrypted=refresh_encrypted,
        token_type="bearer",
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return {"id": account.id, "platform": "youtube"}


# ── Telegram ─────────────────────────────────────────────────────────────────

@router.post("/telegram/send-code")
async def telegram_send_code(
    phone: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
):
    """
    Initiate Telegram phone-based authentication.
    Returns session string and phone_code_hash to be passed to /telegram/verify.
    """
    from app.integrations.telegram.api import telegram_integration
    result = await telegram_integration.start_phone_auth(phone)
    return {
        "session": result["session"],
        "phone_code_hash": result["phone_code_hash"],
        "user_id": str(current_user.id),
    }


@router.post("/telegram/verify")
async def telegram_verify(
    phone: str = Body(...),
    code: str = Body(...),
    session: str = Body(...),
    phone_code_hash: str = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Complete Telegram auth, save encrypted session string as the account token.
    """
    from app.integrations.telegram.api import telegram_integration
    new_session = await telegram_integration.complete_phone_auth(
        phone, code, session, phone_code_hash
    )
    encrypted = token_manager.encrypt(new_session)
    account = SocialAccount(
        user_id=current_user.id,
        platform=Platform.telegram,
        account_id=phone,
        encrypted_token=encrypted,
        token_type="session",
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return {"id": account.id, "platform": "telegram"}

