import logging
import datetime
from qdrant_client.http.models import PointStruct
from core.qdrant_client import get_qdrant_client
from core.config import get_settings
from services.rag.embedder import Embedder
from models.company import Company

settings = get_settings()
logger = logging.getLogger(__name__)

class Indexer:
    def __init__(self, qdrant_client=None, embedder=None):
        self.client = qdrant_client or get_qdrant_client()
        self.embedder = embedder or Embedder()
        self.collection = settings.QDRANT_COLLECTION

    async def index_company(self, company: Company):
        """
        Embed and index a company profile with structured text.
        """
        # 1. Handle growth signals (dict or list)
        signals_text = ""
        if company.growth_signals:
            if isinstance(company.growth_signals, dict):
                signals_text = ". ".join([f"{k}: {v}" for k, v in company.growth_signals.items() if v])
            elif isinstance(company.growth_signals, list):
                signals_text = ". ".join([str(s) for s in company.growth_signals if s])

        # 2. Construct structured profile text for better embedding quality
        profile_text = f"""
        Name: {company.name or 'Unknown'}
        Industry: {company.industry or 'N/A'}
        Business Model: {company.business_model or 'N/A'}
        Target Customer: {company.target_customer or 'N/A'}
        Description: {company.description or 'No description available.'}
        Growth Signals: {signals_text or 'None'}
        """.strip()

        # 3. Generate embedding
        # TODO: Add validation for embedding dimensions (1536)
        embedding = await self.embedder.embed_text(profile_text)

        # 4. Upsert to Qdrant
        # We use the timestamp that was already set on the company object
        # for consistency between DB and Qdrant.
        embedded_at_str = company.embedded_at.isoformat() if company.embedded_at else datetime.datetime.now().isoformat()

        point = PointStruct(
            id=str(company.id),
            vector=embedding,
            payload={
                "company_id": str(company.id),
                "name": company.name,
                "industry": company.industry,
                "business_model": company.business_model,
                "embedded_at": embedded_at_str,
                "profile_text": profile_text
            }
        )

        # TODO: should embedded_at be stablished in the embedder.py file or here?

        await self.client.upsert(
            collection_name=self.collection,
            points=[point]
        )
        logger.info(f"Indexed company {company.id}")

    async def index_documents(self, docs):
        # TODO: Implement index_batch for better performance at scale
        pass

    async def index_documents(self, docs):
        # TODO: Placeholder for future document indexing
        pass
