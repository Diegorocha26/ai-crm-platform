import asyncio
import logging
from datetime import datetime
from sqlalchemy import select
from core.database import AsyncSessionLocal
from models.company import Company
from services.rag.indexer import Indexer

logger = logging.getLogger(__name__)

# Global indexer instance to reuse clients (OpenAI, Redis, Qdrant)
_indexer: Indexer | None = None

def get_indexer() -> Indexer:
    global _indexer
    if _indexer is None:
        _indexer = Indexer()
    return _indexer

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
    try:
        indexer = get_indexer()
        
        # CREATE THE SOURCE OF TRUTH TIMESTAMP HERE
        now = datetime.now()
        # Set it on the detached object so the indexer uses it
        company_data.embedded_at = now
        
        await indexer.index_company(company_data)
        
        # 3. Update Status (New short DB session)
        async with AsyncSessionLocal() as session:
            update_stmt = select(Company).where(Company.id == company_id)
            res = await session.execute(update_stmt)
            company_to_update = res.scalar_one()
            
            # USE THE SAME 'now' VARIABLE
            company_to_update.embedded_at = now
            await session.commit()
            
        logger.info(f"Successfully embedded company {company_id}")
        
    except Exception:
        logger.exception(f"Embedding failed for company {company_id}")
        raise

def process_embedding_job(company_id: str):
    """
    Sync wrapper for RQ worker.
    """
    asyncio.run(process_embedding_job_async(company_id))
