import asyncio
import logging
from qdrant_client.http.models import Distance, VectorParams
from core.qdrant_client import get_qdrant_client
from core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()

async def create_collection():
    client = get_qdrant_client()
    
    collection_name = settings.QDRANT_COLLECTION
    logger.info(f"Creating collection: {collection_name}")
    
    exists = await client.collection_exists(collection_name)
    if not exists:
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )
        logger.info(f"Collection {collection_name} created successfully.")
    else:
        logger.info(f"Collection {collection_name} already exists.")

if __name__ == "__main__":
    asyncio.run(create_collection())
