import json
import structlog
from core.database import AsyncSessionLocal
from models.enrichment import Enrichment, EnrichmentType, EntityType

logger = structlog.get_logger()

# Map prompt names to enrichment types
PROMPT_TYPE_MAP = {
    "company_summary": EnrichmentType.SUMMARY,
    "lead_scoring": EnrichmentType.SCORING,
    "outreach_generation": EnrichmentType.OUTREACH,
}

async def log_call(
    prompt_name: str,
    model: str,
    latency_ms: int,
    raw_output: str,
    parsed_output: dict | None,
    prompt_version: str = "v1",
    entity_id: str | None = None,
    entity_type: str | None = None,
    tokens_used: int | None = None,
    error: str | None = None
):
    """
    Log LLM call details to structlog and optionally to DB.
    """
    
    # 1. Resolve EnrichmentType for logging and DB
    enrich_type = PROMPT_TYPE_MAP.get(prompt_name)
    if not enrich_type:
        logger.warning("unknown_prompt_name_fallback_to_other", prompt_name=prompt_name)
        enrich_type = EnrichmentType.OTHER

    # 2. Structured Logging (First, so we always have a record)
    log_event = {
        "event": "llm_call_complete",
        "prompt_name": prompt_name,
        "prompt_version": prompt_version,
        "enrichment_type": enrich_type.value,
        "model": model,
        "latency_ms": latency_ms,
        "tokens_used": tokens_used,
        "entity_id": entity_id,
        "entity_type": entity_type,
        "success": parsed_output is not None,
        "error": error
    }
    
    if parsed_output is not None:
        logger.info(**log_event)
    else:
        logger.error(**log_event)

    # 3. DB Write (Optional)
    if not entity_id or not entity_type:
        return

    session = None
    try:
        # Resolve EntityType enum
        try:
            db_entity_type = EntityType(entity_type)
        except ValueError:
            logger.error("invalid_entity_type_for_db_logging", entity_type=entity_type)
            return

        # Prepare raw output as valid JSON object for MySQL JSON column
        raw_json_obj = None
        if raw_output:
            try:
                raw_json_obj = json.loads(raw_output)
            except json.JSONDecodeError:
                raw_json_obj = {"_raw_text_fallback": raw_output}

        # Create record
        async with AsyncSessionLocal() as session:
            enrichment = Enrichment(
                entity_id=entity_id,
                entity_type=db_entity_type,
                enrichment_type=enrich_type,
                prompt_version=prompt_version,
                raw_llm_output=raw_json_obj,
                parsed_output=parsed_output,
                model_used=model,
                tokens_used=tokens_used,
                latency_ms=latency_ms
            )
            session.add(enrichment)
            await session.commit()
            
    except Exception as e:
        if session:
            await session.rollback()
        logger.error("failed_to_log_enrichment_to_db", error=str(e), entity_id=entity_id)
