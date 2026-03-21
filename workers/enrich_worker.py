import asyncio
import traceback
from datetime import datetime
import structlog
from rq import get_current_job
from core.redis_client import get_queue
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
        
        # Handle manual DLQ logic
        # Note: The Orchestrator sets DB status to FAILED, but we also want to preserve the job payload
        try:
            dlq = get_queue(QUEUE_DLQ)
            dlq.enqueue(
                "workers.enrich_worker.dead_letter_handler",
                job_id=job_id,
                company_id=company_id,
                error=str(e),
                failed_at=datetime.utcnow(),
                origin_queue="enrich"
            )
            log.info("job_moved_to_dlq")
        except Exception as dlq_error:
            log.error("dlq_push_failed", error=str(dlq_error))
        
        # Re-raise to ensure RQ marks it as failed in its own registry too
        raise

def dead_letter_handler(**kwargs):
    """
    Placeholder handler for jobs in DLQ.
    This function exists just to have a valid entry point for the DLQ jobs.
    In reality, we just inspect the payload.
    """
    pass
