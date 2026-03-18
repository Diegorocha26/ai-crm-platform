import structlog

logger = structlog.get_logger()

def process_enrichment_job(company_id: str):
    """
    Stub for enrichment worker. To be implemented in Phase 5.
    """
    from rq import get_current_job
    job = get_current_job()
    logger.info("processing_enrichment_job", company_id=company_id)
    # TODO: Implement enrichment logic
