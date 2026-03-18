import asyncio
import traceback
import json
from datetime import datetime, timezone
from sqlalchemy.future import select
from core.database import AsyncSessionLocal
from core.redis_client import sync_redis_client
from workers.queues import QUEUE_DLQ
from services.scraper.website_scraper import WebsiteScraper
from models.company import Company, EnrichmentStatus
from services.ingestion.publisher import publish_enrichment_job
import structlog

logger = structlog.get_logger()

async def _scrape_and_save(company_id: str, url: str):
    """
    Async logic to scrape website and save raw data to DB.
    """
    scraper = WebsiteScraper()
    await scraper.start()
    try:
        raw_data = await scraper.scrape(url)
        
        async with AsyncSessionLocal() as session:
            stmt = select(Company).where(Company.id == company_id)
            result = await session.execute(stmt)
            company = result.scalar_one_or_none()
            
            if company:
                company.raw_html = raw_data.raw_html
                if raw_data.name:
                    company.name = raw_data.name
                if raw_data.description:
                    company.description = raw_data.description
                
                company.tech_stack = raw_data.detected_tech
                company.social_links = raw_data.social_links
                company.source_url = str(raw_data.website)
                
                # TODO: Set status to PROCESSING here or at the start of enrichment
                # For now, we leave it as is so enrichment worker can handle status transitions
                
                await session.commit()
            else:
                raise ValueError(f"Company {company_id} not found")
                
    finally:
        await scraper.close()

async def _mark_as_failed(company_id: str):
    """
    Mark company enrichment status as FAILED in DB.
    """
    async with AsyncSessionLocal() as session:
        stmt = select(Company).where(Company.id == company_id)
        result = await session.execute(stmt)
        company = result.scalar_one_or_none()
        if company:
            company.enrichment_status = EnrichmentStatus.FAILED
            await session.commit()

def process_scrape_job(company_id: str, url: str):
    """
    RQ Worker entry point for scraping jobs.
    Handles async execution and DLQ logic.
    """
    from rq import get_current_job

    job = get_current_job()
    logger.info("processing_scrape_job", company_id=company_id, url=url)
    
    try:
        asyncio.run(_scrape_and_save(company_id, url))
        
        # Trigger next stage (Enrichment)
        try:
            publish_enrichment_job(company_id)
        except Exception as e:
            logger.error("failed_to_publish_enrichment_job", error=str(e), company_id=company_id)
            raise

        logger.info("scrape_job_success", company_id=company_id)
        
    except Exception as e:
        logger.error("scrape_job_failed", error=str(e), company_id=company_id)
        
        # DLQ Logic: Only push to DLQ if no retries are left
        # Safety check: job might be None if called outside of a worker context
        if job and job.retries_left <= 0:
            logger.error("max_retries_exceeded", company_id=company_id)
            
            payload = {
                "company_id": company_id,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "failed_at": datetime.now(timezone.utc).isoformat()
            }
            # Push to Redis List for manual inspection
            sync_redis_client.lpush(QUEUE_DLQ, json.dumps(payload))
            
            # Update DB status
            try:
                asyncio.run(_mark_as_failed(company_id))
            except Exception as db_err:
                logger.error("failed_to_update_db_status", error=str(db_err))
        
        # Re-raise so RQ handles retries or marks as failed in its internal registry
        raise
