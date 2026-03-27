import logging
from typing import List, Dict, Any, Tuple
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from sqlalchemy import select
from core.qdrant_client import get_qdrant_client
from core.config import get_settings
from core.database import AsyncSessionLocal
from services.rag.embedder import Embedder
from models.company import Company

settings = get_settings()
logger = logging.getLogger(__name__)

# Global embedder instance to reuse clients
_embedder: Embedder | None = None

def get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = Embedder()
    return _embedder

class RetrievedChunk:
    def __init__(self, id: str, score: float, payload: Dict[str, Any]):
        self.id = id
        self.score = score
        self.payload = payload
    
    def __repr__(self):
        return f"<RetrievedChunk id={self.id} score={self.score}>"

class Retriever:
    def __init__(self):
        self.client = get_qdrant_client()
        self.collection = settings.QDRANT_COLLECTION

    async def search(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        """
        Semantic search for companies using query_points.
        Returns an empty list if embedding or search fails.
        """
        try:
            query = query.strip()
            if not query:
                return []

            # 1. Generate embedding (External API call)
            # TODO: Add retry logic for embedding failures
            embedding = await get_embedder().embed_text(query)
            
            # 2. Query Qdrant
            response = await self.client.query_points(
                collection_name=self.collection,
                query=embedding,
                limit=top_k
            )
            
            return [RetrievedChunk(str(r.id), r.score, r.payload) for r in response.points]

        except Exception:
            logger.exception(f"Semantic search failed for query: '{query}'")
            return []

    async def search_similar_companies(
        self, 
        company_id: str, 
        top_k: int = 5
    ) -> List[Tuple[Company, float]]:
        """
        Find companies similar to a given company ID.
        Returns a list of (Company, score) tuples.
        """
        try:
            # Exclude the target company from results (self-match)
            search_filter = Filter(
                must_not=[
                    FieldCondition(
                        key="company_id",
                        match=MatchValue(value=company_id)
                    )
                ]
            )

            response = await self.client.query_points(
                collection_name=self.collection,
                query=company_id,
                query_filter=search_filter,
                limit=top_k
            )
            
            # Map of ID -> Score
            id_score_map = {str(r.id): r.score for r in response.points}
            ids = list(id_score_map.keys())
            
            if not ids:
                return []
            
            # TODO: Consider storing essential fields in Qdrant payload to avoid DB hit
            async with AsyncSessionLocal() as session:
                query = select(Company).where(Company.id.in_(ids))
                db_results = await session.execute(query)
                companies = db_results.scalars().all()
                
                # Sort by score order
                ordered = []
                company_map = {str(c.id): c for c in companies}
                for id_ in ids:
                    if id_ in company_map:
                        ordered.append((company_map[id_], id_score_map[id_]))
                    else:
                        logger.warning(f"Company {id_} found in Qdrant but missing in MySQL")
                
                return ordered
                
        except Exception:
            logger.exception(f"Similarity search failed for company {company_id}")
            return []

    async def search_by_industry(self, industry: str, top_k: int = 10) -> List[RetrievedChunk]:
        """
        Search for companies in a specific industry using ranked query_points.
        """
        # Note: We use a zero-vector or generic embedding if we only want 
        # filter-based retrieval, but query_points with only filter is valid.
        response = await self.client.query_points(
            collection_name=self.collection,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="industry",
                        match=MatchValue(value=industry)
                    )
                ]
            ),
            limit=top_k
        )
        return [RetrievedChunk(str(r.id), r.score, r.payload) for r in response.points]
