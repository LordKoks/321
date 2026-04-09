import asyncio
import logging
from datetime import datetime, timezone, date
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _collect():
    from sqlalchemy import select, and_
    from app.database import AsyncSessionLocal
    from app.models.post import PostTarget, PostTargetStatus
    from app.models.social_account import SocialAccount
    from app.models.analytics import Analytics
    from app.core.token_manager import token_manager
    from app.integrations.vk.api import vk_integration
    from app.integrations.x.api import x_integration
    from app.integrations.ok.api import ok_integration
    from app.integrations.youtube.api import youtube_integration

    integration_map = {
        "vk": vk_integration,
        "x": x_integration,
        "ok": ok_integration,
        "youtube": youtube_integration,
    }

    today = date.today()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(PostTarget).where(PostTarget.status == PostTargetStatus.published)
        )
        targets = result.scalars().all()
        logger.info("Collecting analytics for %d published targets", len(targets))

        for target in targets:
            acc_result = await db.execute(
                select(SocialAccount).where(SocialAccount.id == target.social_account_id)
            )
            account = acc_result.scalar_one_or_none()
            if not account or not account.encrypted_token:
                continue

            integration = integration_map.get(account.platform.value)
            if not integration:
                continue

            try:
                token = token_manager.decrypt(account.encrypted_token)
                from app.models.post import Post
                post_result = await db.execute(
                    select(Post).where(Post.id == target.post_id)
                )
                post = post_result.scalar_one_or_none()
                platform_ids = dict(post.platform_post_ids or {}) if post else {}
                post_platform_id = platform_ids.get(str(account.id))
                if not post_platform_id:
                    continue

                stats = await integration.get_post_stats(
                    token, post_platform_id, account.extra_data
                )
                record = Analytics(
                    social_account_id=account.id,
                    post_target_id=target.id,
                    date=today,
                    likes=stats.get("likes", 0),
                    views=stats.get("views", 0),
                    shares=stats.get("shares", 0),
                    comments=stats.get("comments", 0),
                    reach=stats.get("reach", 0),
                )
                db.add(record)
            except Exception as exc:
                logger.exception("Failed to collect analytics for target %s", target.id)

        await db.commit()


@celery_app.task(name="app.tasks.analytics.collect_analytics")
def collect_analytics():
    asyncio.run(_collect())
