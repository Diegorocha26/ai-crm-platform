import logging
from typing import Any, Dict
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from services.agents.base_agent import BaseAgent
from models.lead import Lead
from models.generated_content import GeneratedContent, ContentType
from schemas.llm_output import OutreachOutput

logger = logging.getLogger(__name__)

class OutreachAgent(BaseAgent):
    """
    Agent responsible for generating personalized outreach emails for leads.
    Chains data retrieval, RAG context, and LLM generation.
    """
    async def run(self, task: Dict[str, Any]) -> OutreachOutput:
        """
        task should contain:
        - lead_id: The UUID of the lead to outreach.
        - value_proposition: (Optional) The core value to highlight.
        """
        lead_id = task.get("lead_id")
        value_proposition = task.get("value_proposition", "Our AI-powered CRM solution helps automate sales workflows.")
        
        if not lead_id:
            raise ValueError("lead_id is required in task")

        # TODO: use try blocks to garentee rollbacks in case somethings goes wrong
        async with self.db_session_factory() as session:
            # 1. Fetch Lead + Company context
            result = await session.execute(
                select(Lead)
                .options(selectinload(Lead.company))
                .where(Lead.id == lead_id)
            )
            lead = result.scalar_one_or_none()
            
            if not lead:
                raise ValueError(f"Lead with id {lead_id} not found")

            company = lead.company

            # 2. RAG Retrieval for more context (recent news or similar company insights)
            # We search for company description + news to find relevant personalization hooks
            search_query = f"{company.name} {company.industry} recent news and business strategy"
            retrieved_chunks = await self.retriever.search(search_query, top_k=3)
            
            context_text = "\n".join([c.payload.get("description", "") for c in retrieved_chunks if c.payload])
            if not context_text:
                context_text = company.description or "No additional context found."

            # 3. Prepare variables for LLM
            variables = {
                "lead_name": lead.full_name,
                "lead_role": lead.role or "Stakeholder",
                "company_name": company.name,
                "value_proposition": value_proposition,
                "context": context_text
            }

            # 4. Call LLM
            self._log_info(f"Generating outreach for lead {lead_id} at {company.name}")
            outreach_result: OutreachOutput = await self.llm.complete(
                prompt_name="outreach_generation",
                variables=variables,
                entity_id=lead_id,
                entity_type="lead"
            )

            # 5. Save generated content to DB
            generated_content = GeneratedContent(
                lead_id=lead_id,
                content_type=ContentType.OUTREACH_EMAIL,
                content=outreach_result.body, # We store the body, or could store the whole JSON
                prompt_version="v1",
                model_used=self.llm.client.model if hasattr(self.llm.client, 'model') else "gpt-4o-mini" # Fallback if model not exposed
            )
            

            # TODO: change this part below
            # Need to get model name properly from template since client doesn't store it directly in that way
            # Actually, llm.complete already handles logging to enrichments. 
            # But we want to store it in generated_content as well.
            
            template = self.llm.registry.load_prompt("outreach_generation", "v1")
            generated_content.model_used = template.model

            session.add(generated_content)
            await session.commit()

            return outreach_result
