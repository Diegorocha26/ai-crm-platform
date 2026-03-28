import redis.asyncio as aioredis
from redis import Redis
from core.config import get_settings

settings = get_settings()

# Global sync client for RQ (Must NOT use decode_responses=True for RQ/Pickle compatibility)
sync_redis_client = Redis.from_url(settings.REDIS_URL)

# Global async client (lazy initialization)
_async_redis_client: aioredis.Redis | None = None

def get_redis_client(force_new: bool = False) -> aioredis.Redis:
    """Get or create an async Redis client."""
    global _async_redis_client
    if force_new or _async_redis_client is None:
        client = aioredis.from_url(
            settings.REDIS_URL, 
            encoding="utf-8", 
            decode_responses=True,
            max_connections=20
        )
        if force_new:
            return client
        _async_redis_client = client
    return _async_redis_client

def get_queue(name: str):
    """Get an RQ Queue with the sync Redis connection."""
    from rq import Queue
    return Queue(name, connection=sync_redis_client)
