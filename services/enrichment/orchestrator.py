import asyncio
import logging
import traceback
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import AsyncSessionLocal
from core.config import get_settings
from models.company import Company, EnrichmentStatus
from models.enrichment import Enrichment, EnrichmentType, EntityType
from services.llm.client import LLMClient
from services.enrichment.external_apis.base import BaseEnrichmentProvider
from services.enrichment.external_apis.mock import MockEnrichmentProvider
# from services.enrichment.external_apis.hunter import HunterEnrichmentProvider  # TODO: Implement later
from services.ingestion.publisher import publish_embedding_job

settings = get_settings()
logger = logging.getLogger(__name__)

def get_enrichment_provider() -> BaseEnrichmentProvider:
    if settings.ENRICHMENT_PROVIDER == "hunter":
        # TODO: Implement Hunter provider
        # return HunterEnrichmentProvider(api_key=settings.HUNTER_API_KEY)
        logger.warning("Hunter provider requested but not implemented. Falling back to mock.")
        return MockEnrichmentProvider()
    return MockEnrichmentProvider()

class EnrichmentOrchestrator:
    def __init__(self):
        self.llm_client = LLMClient()
        self.enrichment_provider = get_enrichment_provider()

    async def enrich_company(self, company_id: str):
        """
        Orchestrate the enrichment pipeline for a company.
        Handles both LLM enrichment and external API data fetching.
        """
        async with AsyncSessionLocal() as session:
            # 1. Fetch Company
            result = await session.execute(select(Company).where(Company.id == company_id))
            company = result.scalar_one_or_none()
            
            if not company:
                logger.error(f"Company {company_id} not found")
                return

            # Update status to processing
            company.enrichment_status = EnrichmentStatus.PROCESSING
            await session.commit()

            try:
                # 2. Run Enrichment Tasks in Parallel
                llm_task = self._enrich_with_llm(company, session)
                email_task = self._enrich_emails(company, session)
                
                results = await asyncio.gather(llm_task, email_task, return_exceptions=True)
                
                llm_result, email_result = results
                
                # 3. Handle Partial Success
                success_count = 0
                errors = []

                if isinstance(llm_result, Exception):
                    logger.error(f"LLM Enrichment failed for {company_id}: {llm_result}")
                    errors.append(f"LLM: {str(llm_result)}")
                else:
                    success_count += 1

                if isinstance(email_result, Exception):
                    logger.error(f"Email Enrichment failed for {company_id}: {email_result}")
                    errors.append(f"Email: {str(email_result)}")
                else:
                    success_count += 1
                
                # 4. Final Status Update
                if success_count == 2:
                    company.enrichment_status = EnrichmentStatus.DONE
                elif success_count > 0:
                    company.enrichment_status = EnrichmentStatus.DONE  # Treated as done but with partial data
                    logger.warning(f"Enrichment partial success for {company_id}. Errors: {errors}")
                else:
                    company.enrichment_status = EnrichmentStatus.FAILED
                    logger.error(f"Enrichment failed completely for {company_id}")
                
                company.updated_at = datetime.now()
                await session.commit()
                
                # 5. Trigger Next Stage (Embeddings) if at least partial success
                if success_count > 0:
                    publish_embedding_job(company_id)

            except Exception as e:
                logger.error(f"Critical error in enrichment orchestrator: {traceback.format_exc()}")
                company.enrichment_status = EnrichmentStatus.FAILED
                await session.commit()
                raise e

    async def _enrich_with_llm(self, company: Company, session: AsyncSession):
        """Call LLM to summarize company data."""
        if not company.raw_html:
            raise ValueError(f"Missing raw_html for company {company.id}")

        # Prepare prompt variables
        variables = {
            "website_content": company.raw_html[:15000]  # Truncate to avoid token limits
        }
        
        # Call LLM
        response = await self.llm_client.complete(
            prompt_name="company_summary",
            variables=variables,
            entity_id=str(company.id),
            entity_type="company"
        )
        
        # Parse output is already done by client, response is a Pydantic model (CompanySummaryOutput)
        # Update Company model
        company.industry = response.industry
        company.business_model = response.business_model
        company.target_customer = response.target_customer
        company.description = response.product_description
        company.tech_stack = response.tech_stack
        company.growth_signals = response.growth_signals
        
        # Save enrichment log
        enrichment_record = Enrichment(
            entity_id=str(company.id),
            entity_type=EntityType.COMPANY,
            enrichment_type=EnrichmentType.SUMMARY,
            prompt_version="v1", # TODO: Get from client response
            parsed_output=response.model_dump(),
            model_used=settings.OPENAI_MODEL,
        )
        session.add(enrichment_record)
        
    async def _enrich_emails(self, company: Company, session: AsyncSession):
        """Call external API to find emails."""
        if not company.website:
            raise ValueError(f"Missing website for company {company.id}")

        domain = company.website.replace("https://", "").replace("http://", "").split("/")[0]
        
        emails = await self.enrichment_provider.find_emails(domain)
        
        # Merge into social_links or similar field
        current_links = company.social_links or {}
        if isinstance(current_links, list):
             current_links = {"links": current_links}
        
        current_links["emails"] = [e.model_dump() for e in emails]
        company.social_links = current_links
        
        # Log this enrichment action? Maybe not needed for simple API lookup, 
        # but good for audit.
        enrichment_record = Enrichment(
            entity_id=str(company.id),
            entity_type=EntityType.COMPANY,
            enrichment_type=EnrichmentType.OTHER, # or OUTREACH/CONTACT
            prompt_version="n/a",
            parsed_output={"emails": [e.model_dump() for e in emails]},
            model_used=settings.ENRICHMENT_PROVIDER
        )
        session.add(enrichment_record)
