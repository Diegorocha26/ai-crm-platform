import logging
from qdrant_client import AsyncQdrantClient
from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_client: AsyncQdrantClient | None = None

def get_qdrant_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        logger.info(f"Connecting to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
        _client = AsyncQdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )
    return _client
