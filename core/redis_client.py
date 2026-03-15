import redis.asyncio as aioredis
from redis import Redis
from core.config import get_settings

settings = get_settings()

# Global sync client for RQ
sync_redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)

# Global async client (lazy initialization)
_async_redis_client: aioredis.Redis | None = None

def get_redis_client() -> aioredis.Redis:
    """Get or create a global async Redis client."""
    global _async_redis_client
    if _async_redis_client is None:
        _async_redis_client = aioredis.from_url(
            settings.REDIS_URL, 
            encoding="utf-8", 
            decode_responses=True,
            max_connections=20
        )
    return _async_redis_client

def get_queue(name: str):
    """Get an RQ Queue with the sync Redis connection."""
    from rq import Queue
    return Queue(name, connection=sync_redis_client)
