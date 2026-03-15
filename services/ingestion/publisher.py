from workers.queues import QUEUE_SCRAPE, QUEUE_ENRICH, QUEUE_EMBED, QUEUE_CONFIG
from core.redis_client import get_queue

def enqueue_job(queue_name: str, job_path: str, **kwargs):
    from rq import Retry
    queue = get_queue(queue_name)
    config = QUEUE_CONFIG[queue_name]

    job = queue.enqueue(
        job_path,
        **kwargs,
        job_timeout=config["timeout"],
        retry=Retry(max=config["retry"])
    )

    return job

def publish_scrape_job(company_id: str, url: str) -> str:
    """
    Publish a scraping job to the queue.
    """
    job = enqueue_job(
        QUEUE_SCRAPE,
        "workers.scrape_worker.process_scrape_job",
        company_id=company_id,
        url=url
    )
    return job.id

def publish_enrichment_job(company_id: str) -> str:
    """
    Publish an enrichment job to the queue.
    """
    job = enqueue_job(
            QUEUE_ENRICH,
            "workers.enrich_worker.process_enrichment_job",
            company_id=company_id
        )
    return job.id

def publish_embedding_job(company_id: str) -> str:
    """
    Publish an embedding job to the queue.
    """
    job = enqueue_job(
        QUEUE_EMBED,
        "workers.embedding_worker.process_embedding_job",
        company_id=company_id
    )
    return job.id
