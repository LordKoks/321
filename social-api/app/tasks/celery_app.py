from celery import Celery
from app.config import settings

celery_app = Celery(
    "social_api",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.scheduler", "app.tasks.analytics"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "publish-scheduled-posts": {
            "task": "app.tasks.scheduler.publish_scheduled_posts",
            "schedule": 60.0,
        },
        "collect-analytics": {
            "task": "app.tasks.analytics.collect_analytics",
            "schedule": 3600.0,
        },
    },
)
