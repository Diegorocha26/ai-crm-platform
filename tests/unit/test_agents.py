import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from services.agents.outreach_agent import OutreachAgent
from services.agents.scoring_agent import ScoringAgent
from services.agents.similarity_agent import SimilarityAgent
from models.lead import Lead, SeniorityLevel
from models.company import Company
from models.generated_content import GeneratedContent, ContentType
from schemas.llm_output import OutreachOutput, LeadScoreOutput

@pytest.fixture
def mock_llm_client():
    client = AsyncMock()
    client.registry = MagicMock()
    # Mock registry.load_prompt to return a template with 'model' attribute
    mock_template = MagicMock()
    mock_template.model = "gpt-4o-mini"
    client.registry.load_prompt.return_value = mock_template
    return client

@pytest.fixture
def mock_retriever():
    retriever = AsyncMock()
    retriever.search.return_value = []
    retriever.search_similar_companies.return_value = []
    return retriever

@pytest.mark.asyncio
async def test_outreach_agent_run(db_session, mock_llm_client, mock_retriever):
    # Setup test data
    company_id = str(uuid.uuid4())
    company = Company(id=company_id, name="Test Company", website=f"test-{uuid.uuid4()}.com", industry="Tech")
    db_session.add(company)
    
    lead_id = str(uuid.uuid4())
    lead = Lead(id=lead_id, company_id=company_id, full_name="John Doe", role="CTO")
    db_session.add(lead)
    await db_session.commit()

    # Mock LLM response
    mock_llm_client.complete.return_value = OutreachOutput(
        subject="Hello John",
        body="This is a test email.",
        tone="professional",
        personalization_hooks=["CTO at Test Company"]
    )

    agent = OutreachAgent(llm_client=mock_llm_client, retriever=mock_retriever)
    # Override db_session_factory for the agent instance to use the test session
    agent.db_session_factory = lambda: db_session

    result = await agent.run({"lead_id": lead_id})

    assert isinstance(result, OutreachOutput)
    assert result.subject == "Hello John"
    
    # Verify GeneratedContent was saved
    from sqlalchemy import select
    res = await db_session.execute(select(GeneratedContent).where(GeneratedContent.lead_id == lead_id))
    content = res.scalar_one_or_none()
    assert content is not None
    assert content.content_type == ContentType.OUTREACH_EMAIL
    assert content.content == "This is a test email."

@pytest.mark.asyncio
async def test_scoring_agent_run(db_session, mock_llm_client, mock_retriever):
    # Setup test data
    company_id = str(uuid.uuid4())
    company = Company(id=company_id, name="Test Company", website=f"test-{uuid.uuid4()}.com", industry="Tech")
    db_session.add(company)
    
    lead_id = str(uuid.uuid4())
    # Seniority set to VP to test boost
    lead = Lead(id=lead_id, company_id=company_id, full_name="Jane Doe", role="VP Engineering", seniority=SeniorityLevel.VP)
    db_session.add(lead)
    await db_session.commit()

    # Mock LLM response: Base score 7.0
    mock_llm_client.complete.return_value = LeadScoreOutput(
        score=7.0,
        reasoning="Good fit.",
        key_factors=["Role matches"],
        recommended_action="reach_out"
    )

    agent = ScoringAgent(llm_client=mock_llm_client, retriever=mock_retriever)
    agent.db_session_factory = lambda: db_session

    result = await agent.run({"lead_id": lead_id})

    # Expected: 7.0 (base) + 1.0 (VP boost) = 8.0
    assert result.score == 8.0
    assert "[Boosted +1.0 for executive seniority]" in result.reasoning
    
    # Verify Lead was updated
    updated_lead = await db_session.get(Lead, lead_id)
    assert updated_lead.relevance_score == 8.0

@pytest.mark.asyncio
async def test_similarity_agent_run(mock_llm_client, mock_retriever):
    company_id = str(uuid.uuid4())
    similar_company = Company(id=str(uuid.uuid4()), name="Similar Inc", website="similar.com")
    
    mock_retriever.search_similar_companies.return_value = [(similar_company, 0.95)]
    
    agent = SimilarityAgent(llm_client=mock_llm_client, retriever=mock_retriever)
    
    result = await agent.run({"company_id": company_id, "top_k": 3})
    
    assert len(result) == 1
    assert result[0][0].name == "Similar Inc"
    assert result[0][1] == 0.95
    mock_retriever.search_similar_companies.assert_called_with(company_id=company_id, top_k=3)


# TODO: check