import logging
from typing import Any, Dict, List, Tuple

from services.agents.base_agent import BaseAgent
from models.company import Company

logger = logging.getLogger(__name__)

class SimilarityAgent(BaseAgent):
    """
    Agent responsible for finding companies similar to a target company.
    Leverages vector search (RAG) and database hydration.
    """
    async def run(self, task: Dict[str, Any]) -> List[Tuple[Company, float]]:
        """
        task should contain:
        - company_id: The UUID of the source company.
        - top_k: (Optional) Number of similar companies to find.
        """
        company_id = task.get("company_id")
        top_k = task.get("top_k", 5)
        
        if not company_id:
            raise ValueError("company_id is required in task")

        self._log_info(f"Finding companies similar to {company_id}")
        
        # 1. Use Retriever to find similar companies from vector store
        # 2. Retriever already handles hydration from MySQL
        similar_companies = await self.retriever.search_similar_companies(
            company_id=company_id,
            top_k=top_k
        )
        
        return similar_companies
