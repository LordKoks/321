import time
import redis.asyncio as aioredis
from app.config import settings

_LIMITS: dict[str, tuple[int, int]] = {
    "vk": (3, 1),
    "x": (300, 10800),
    "youtube": (10000, 86400),
    "ok": (5, 1),
    "telegram": (20, 1),
}


class RateLimiter:
    def __init__(self) -> None:
        self._redis: aioredis.Redis | None = None

    def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    async def is_allowed(self, platform: str, account_id: str, cost: int = 1) -> bool:
        max_requests, window_seconds = _LIMITS.get(platform, (100, 60))
        redis = self._get_redis()
        key = f"rate:{platform}:{account_id}"
        now = time.time()
        window_start = now - window_seconds

        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        _, current_count = await pipe.execute()

        if current_count + cost > max_requests:
            return False

        pipe = redis.pipeline()
        for _ in range(cost):
            pipe.zadd(key, {str(now): now})
        pipe.expire(key, window_seconds + 1)
        await pipe.execute()
        return True

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()


rate_limiter = RateLimiter()
