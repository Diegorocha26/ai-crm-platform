import logging
from typing import Any, Dict
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from services.agents.base_agent import BaseAgent
from models.lead import Lead, SeniorityLevel
from schemas.llm_output import LeadScoreOutput

logger = logging.getLogger(__name__)

class ScoringAgent(BaseAgent):
    """
    Agent responsible for scoring leads based on fit and relevance.
    Chains LLM scoring with rule-based adjustments.
    """
    async def run(self, task: Dict[str, Any]) -> LeadScoreOutput:
        """
        task should contain:
        - lead_id: The UUID of the lead to score.
        """
        lead_id = task.get("lead_id")
        
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

            # 2. Retrieve industry benchmarks or context from RAG
            search_query = f"Ideal Customer Profile for SaaS in {company.industry} and {company.business_model}"
            retrieved_chunks = await self.retriever.search(search_query, top_k=2)
            
            # TODO: (Context can be used in the prompt variables if desired, for now kept simple)

            # 3. Call LLM for base score
            variables = {
                "lead_name": lead.full_name,
                "lead_role": lead.role or "Unknown",
                "company_name": company.name,
                "company_industry": company.industry or "Unknown",
                "company_description": company.description or "No description available"
            }

            self._log_info(f"Scoring lead {lead.full_name} from {company.name}")
            score_result: LeadScoreOutput = await self.llm.complete(
                prompt_name="lead_scoring",
                variables=variables,
                entity_id=lead_id,
                entity_type="lead"
            )

            # 4. Apply rule-based adjustments (e.g., Seniority boost)
            final_score = score_result.score
            
            # Boost for high seniority (VP, CXO)
            if lead.seniority in [SeniorityLevel.VP, SeniorityLevel.CXO]:
                final_score += 1.0
                score_result.reasoning += " [Boosted +1.0 for executive seniority]"
            elif lead.seniority == SeniorityLevel.ENTRY:
                final_score -= 1.0
                score_result.reasoning += " [Reduced -1.0 for entry-level seniority]"

            # Cap the score at 10.0 and minimum at 1.0
            final_score = max(1.0, min(10.0, final_score))
            score_result.score = final_score

            # 5. Update Lead record
            lead.relevance_score = final_score
            # Optional: We could also update buying_power_score separately if needed
            
            session.add(lead)
            await session.commit()

            return score_result
