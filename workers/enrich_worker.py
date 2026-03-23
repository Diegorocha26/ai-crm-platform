import asyncio
import traceback
import json
from datetime import datetime, timezone
import structlog
from rq import get_current_job
from core.redis_client import sync_redis_client
from services.enrichment.orchestrator import EnrichmentOrchestrator
from workers.queues import QUEUE_DLQ

logger = structlog.get_logger()

async def _run_enrichment(company_id: str):
    orchestrator = EnrichmentOrchestrator()
    await orchestrator.enrich_company(company_id)

def process_enrichment_job(company_id: str):
    """
    RQ worker entry point for enrichment jobs.
    Wraps the async orchestrator call in a sync function.
    """
    job = get_current_job()
    job_id = job.id if job else "unknown"
    
    log = logger.bind(job_id=job_id, company_id=company_id, worker="enrich")
    log.info("enrichment_started")

    try:
        asyncio.run(_run_enrichment(company_id))
        log.info("enrichment_completed")
    except Exception as e:
        log.error("enrichment_failed", error=str(e), traceback=traceback.format_exc())
        
        # DLQ Logic: Only push to DLQ if no retries are left
        if job and job.retries_left <= 0:
            log.error("max_retries_exceeded", company_id=company_id)
            
            try:
                payload = {
                    "company_id": company_id,
                    "job_id": job_id,
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "failed_at": datetime.now(timezone.utc).isoformat(),
                    "origin_queue": "enrich"
                }
                # Push to Redis List for manual inspection
                sync_redis_client.lpush(QUEUE_DLQ, json.dumps(payload))
                log.info("job_moved_to_dlq")
            except Exception as dlq_error:
                log.error("dlq_push_failed", error=str(dlq_error))
        
        # Re-raise to ensure RQ handles retries or marks as failed in its internal registry
        raise

def dead_letter_handler(**kwargs):
    """
    Placeholder handler for jobs in DLQ.
    This function exists just to have a valid entry point for the DLQ jobs.
    In reality, we just inspect the payload.
    """
    pass
