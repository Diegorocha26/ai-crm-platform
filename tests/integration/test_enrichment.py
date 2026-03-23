import pytest
import uuid
from sqlalchemy import select
from models.company import Company, EnrichmentStatus
from services.enrichment.orchestrator import EnrichmentOrchestrator

@pytest.mark.asyncio
async def test_enrichment_orchestrator_mock(db_session):
    # 1. Setup
    company_id = str(uuid.uuid4())
    company = Company(
        id=company_id,
        name="Test Corp",
        website="https://test-corp.com",
        raw_html="<html><body><h1>Test Corp</h1><p>We build widgets.</p></body></html>"
    )
    db_session.add(company)
    await db_session.commit()

    # 2. Execute
    orchestrator = EnrichmentOrchestrator()
    await orchestrator.enrich_company(company_id)

    # 3. Verify
    # We need to expire the object to ensure it re-fetches from the DB
    # because the orchestrator uses its own session.
    db_session.expire_all()
    result = await db_session.execute(select(Company).where(Company.id == company_id))      
    updated_company = result.scalar_one()
    assert updated_company.enrichment_status == EnrichmentStatus.DONE
    
    # Check if mock email data was added
    assert updated_company.social_links is not None
    assert "emails" in updated_company.social_links
    assert updated_company.social_links["emails"][0]["email"] == "contact@test-corp.com"

    # TODO: Implement proper LLM mocking to verify specific enriched fields (industry, etc.)
    # without relying on real API calls or being sensitive to missing API keys.
