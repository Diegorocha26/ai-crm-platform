import structlog

logger = structlog.get_logger()

def process_embedding_job(company_id: str):
    """
    Stub for embedding worker. To be implemented in Phase 6.
    """
    from rq import get_current_job
    job = get_current_job()
    logger.info("processing_embedding_job", company_id=company_id)
    # TODO: Implement embedding logic
