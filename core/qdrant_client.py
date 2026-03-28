import logging
from qdrant_client import AsyncQdrantClient
from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_client: AsyncQdrantClient | None = None

def get_qdrant_client(force_new: bool = False) -> AsyncQdrantClient:
    global _client
    if force_new or _client is None:
        logger.info(f"Connecting to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
        client = AsyncQdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )
        if force_new:
            return client
        _client = client
    return _client
