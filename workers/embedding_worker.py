import asyncio
import logging
from datetime import datetime
from sqlalchemy import select
from core.database import AsyncSessionLocal
from core.redis_client import get_redis_client
from core.qdrant_client import get_qdrant_client
from models.company import Company
from services.rag.embedder import Embedder
from services.rag.indexer import Indexer

logger = logging.getLogger(__name__)

async def process_embedding_job_async(company_id: str):
    logger.info(f"Starting embedding job for company {company_id}")
    
    # 1. Fetch Company (Short DB session)
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Company).where(Company.id == company_id))
        company = result.scalar_one_or_none()
        
        if not company:
            logger.error(f"Company {company_id} not found")
            return
        
        # Detach/Copy for external work
        company_data = company 

    # 2. Perform expensive external work (NO DB session open here)
    # We create fresh clients for THIS event loop to avoid "loop closed" errors
    redis_client = get_redis_client(force_new=True)
    qdrant_client = get_qdrant_client(force_new=True)
    
    try:
        embedder = Embedder(redis_client=redis_client)
        indexer = Indexer(qdrant_client=qdrant_client, embedder=embedder)
        
        now = datetime.now()
        company_data.embedded_at = now
        
        await indexer.index_company(company_data)
        
        # 3. Update Status (New short DB session)
        async with AsyncSessionLocal() as session:
            update_stmt = select(Company).where(Company.id == company_id)
            res = await session.execute(update_stmt)
            company_to_update = res.scalar_one()
            
            company_to_update.embedded_at = now
            await session.commit()
            
        logger.info(f"Successfully embedded company {company_id}")
        
    except Exception:
        logger.exception(f"Embedding failed for company {company_id}")
        raise
    finally:
        # 4. Clean up connections for this loop
        await redis_client.aclose()
        await qdrant_client.close()

def process_embedding_job(company_id: str):
    """
    Sync wrapper for RQ worker.
    """
    asyncio.run(process_embedding_job_async(company_id))
