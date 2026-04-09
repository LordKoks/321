import asyncio
import logging
from datetime import datetime, timezone
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _publish_scheduled():
    from sqlalchemy import select, and_
    from app.database import AsyncSessionLocal
    from app.models.post import Post, PostTarget, PostStatus, PostTargetStatus
    from app.models.social_account import SocialAccount
    from app.core.token_manager import token_manager
    from app.integrations.vk.api import vk_integration
    from app.integrations.x.api import x_integration
    from app.integrations.telegram.api import telegram_integration
    from app.integrations.ok.api import ok_integration
    from app.integrations.youtube.api import youtube_integration

    integration_map = {
        "vk": vk_integration,
        "x": x_integration,
        "telegram": telegram_integration,
        "ok": ok_integration,
        "youtube": youtube_integration,
    }

    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Post)
            .where(
                and_(
                    Post.status == PostStatus.scheduled,
                    Post.scheduled_at <= now,
                )
            )
        )
        posts = result.scalars().all()
        logger.info("Found %d scheduled posts to publish", len(posts))

        for post in posts:
            target_result = await db.execute(
                select(PostTarget)
                .where(
                    and_(
                        PostTarget.post_id == post.id,
                        PostTarget.status == PostTargetStatus.pending,
                    )
                )
            )
            targets = target_result.scalars().all()

            all_done = True
            any_success = False

            for target in targets:
                acc_result = await db.execute(
                    select(SocialAccount).where(SocialAccount.id == target.social_account_id)
                )
                account = acc_result.scalar_one_or_none()
                if not account or not account.encrypted_token:
                    target.status = PostTargetStatus.failed
                    target.error_message = "Account not found or no token"
                    all_done = False
                    continue

                integration = integration_map.get(account.platform.value)
                if not integration:
                    target.status = PostTargetStatus.failed
                    target.error_message = f"No integration for {account.platform.value}"
                    all_done = False
                    continue

                try:
                    token = token_manager.decrypt(account.encrypted_token)
                    post_id = await integration.publish_post(
                        token,
                        post.content,
                        post.media_urls or [],
                        account.extra_data,
                    )
                    target.status = PostTargetStatus.published
                    target.published_at = now
                    platform_ids = dict(post.platform_post_ids or {})
                    platform_ids[str(account.id)] = post_id
                    post.platform_post_ids = platform_ids
                    any_success = True
                except Exception as exc:
                    logger.exception("Failed to publish post %s to account %s", post.id, account.id)
                    target.status = PostTargetStatus.failed
                    target.error_message = str(exc)[:1000]
                    all_done = False

            if any_success and all_done:
                post.status = PostStatus.published
            elif any_success:
                post.status = PostStatus.published
            else:
                post.status = PostStatus.failed

            await db.commit()


@celery_app.task(name="app.tasks.scheduler.publish_scheduled_posts")
def publish_scheduled_posts():
    asyncio.run(_publish_scheduled())
