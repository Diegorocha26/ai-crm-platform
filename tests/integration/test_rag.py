import pytest
import uuid
from sqlalchemy import select, delete
from models.company import Company
from services.rag.embedder import Embedder
from services.rag.indexer import Indexer
from services.rag.retriever import Retriever
from services.rag.context_builder import ContextBuilder
from core.database import AsyncSessionLocal
from core.redis_client import get_redis_client
from core.qdrant_client import get_qdrant_client
from core.config import get_settings

settings = get_settings()

@pytest.fixture(scope="function")
async def redis_client():
    return get_redis_client(force_new=True)

@pytest.fixture(scope="function")
async def qdrant_client():
    return get_qdrant_client(force_new=True)

@pytest.mark.asyncio
async def test_embedder_caching(redis_client):
    # Inject client to avoid singleton issues
    embedder = Embedder(redis_client=redis_client)
    test_text = f"Test unique string {uuid.uuid4()}"
    
    # First call - should go to OpenAI
    embedding1 = await embedder.embed_text(test_text)
    assert len(embedding1) == 1536
    
    # Check if cached in Redis
    cache_key = embedder._get_cache_key(test_text.strip()[:15000])
    cached_val = await redis_client.get(cache_key)
    assert cached_val is not None
    
    # Second call - should hit Redis
    embedding2 = await embedder.embed_text(test_text)
    assert embedding1 == embedding2

@pytest.mark.asyncio
async def test_rag_full_flow(qdrant_client, redis_client):
    company_id = str(uuid.uuid4())
    name = f"TestAI_{uuid.uuid4().hex[:8]}"
    other_id = None
    
    # Inject clients
    embedder = Embedder(redis_client=redis_client)
    indexer = Indexer(qdrant_client=qdrant_client, embedder=embedder)
    retriever = Retriever(qdrant_client=qdrant_client, embedder=embedder)
    builder = ContextBuilder(retriever=retriever)

    # 1. Seed Company in DB
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Company).where(Company.name == name))
        
        company = Company(
            id=company_id,
            name=name,
            website=f"https://{name}.example.com",
            description="Leading AI research lab for CRM automation.",
            industry="Artificial Intelligence",
            target_customer="Enterprise Sales",
            growth_signals={"funding": "Series B"}
        )
        session.add(company)
        await session.commit()

    try:
        # 2. Index in Qdrant
        await indexer.index_company(company)
        
        # 3. Search by text
        search_results = await retriever.search("CRM automation research", top_k=1)
        assert len(search_results) > 0
        assert search_results[0].payload["company_id"] == company_id
        
        # 4. Search Similar (Should exclude self)
        other_id = str(uuid.uuid4())
        other_name = f"OtherAI_{uuid.uuid4().hex[:8]}"
        async with AsyncSessionLocal() as session:
            other_company = Company(
                id=other_id,
                name=other_name,
                website=f"https://{other_name}.example.com",
                description="AI for sales automation and CRM.",
                industry="Artificial Intelligence"
            )
            session.add(other_company)
            await session.commit()
            await indexer.index_company(other_company)

        similar_results = await retriever.search_similar_companies(company_id, top_k=5)
        found_ids = [str(c.id) for c, score in similar_results]
        assert company_id not in found_ids
        assert other_id in found_ids
        
        # 5. Search by Industry
        industry_results = await retriever.search_by_industry("Artificial Intelligence")
        industry_ids = [r.payload["company_id"] for r in industry_results]
        assert company_id in industry_ids
        assert other_id in industry_ids
        
        # 6. Context Builder
        context = await builder.build_context("CRM research")
        assert name in context
        assert "Leading AI research" in context

    finally:
        # Cleanup
        ids_to_del = [company_id]
        if other_id:
            ids_to_del.append(other_id)
            
        async with AsyncSessionLocal() as session:
            await session.execute(delete(Company).where(Company.id.in_(ids_to_del)))
            await session.commit()
        
        await qdrant_client.delete(
            collection_name=settings.QDRANT_COLLECTION,
            points_selector=ids_to_del
        )
