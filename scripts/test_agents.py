import asyncio
import uuid
from sqlalchemy import select
from core.database import AsyncSessionLocal
from models.lead import Lead, SeniorityLevel
from models.company import Company
from services.agents.outreach_agent import OutreachAgent
from services.agents.scoring_agent import ScoringAgent
from services.agents.similarity_agent import SimilarityAgent

async def seed_test_data():
    async with AsyncSessionLocal() as session:
        # Check if we already have test data
        result = await session.execute(select(Company).where(Company.name == "Agent Test Corp"))
        company = result.scalar_one_or_none()
        
        if not company:
            company = Company(
                id=str(uuid.uuid4()),
                name="Agent Test Corp",
                website="agent-test-corp.com",
                industry="Artificial Intelligence",
                description="A company specializing in AI agents and automation."
            )
            session.add(company)
            
            lead = Lead(
                id=str(uuid.uuid4()),
                company_id=company.id,
                full_name="Agent Smith",
                role="Head of Automation",
                seniority=SeniorityLevel.CXO,
                email="smith@agent-test-corp.com"
            )
            session.add(lead)
            await session.commit()
            print(f"Seeded test company {company.id} and lead {lead.id}")
            return company.id, lead.id
        else:
            result = await session.execute(select(Lead).where(Lead.company_id == company.id))
            lead = result.scalars().first()
            return company.id, lead.id

async def main():
    print("--- Starting Agent Manual Test ---")
    company_id, lead_id = await seed_test_data()
    
    # 1. Test Scoring Agent
    print("\n[Testing ScoringAgent...]")
    scoring_agent = ScoringAgent()
    score_result = await scoring_agent.run({"lead_id": lead_id})
    print(f"Score: {score_result.score}")
    print(f"Reasoning: {score_result.reasoning}")
    
    # 2. Test Outreach Agent
    print("\n[Testing OutreachAgent...]")
    outreach_agent = OutreachAgent()
    outreach_result = await outreach_agent.run({"lead_id": lead_id})
    print(f"Subject: {outreach_result.subject}")
    print(f"Body snippet: {outreach_result.body[:200]}...")
    
    # 3. Test Similarity Agent
    print("\n[Testing SimilarityAgent...]")
    similarity_agent = SimilarityAgent()
    similar_companies = await similarity_agent.run({"company_id": company_id, "top_k": 3})
    print(f"Found {len(similar_companies)} similar companies.")
    for c, score in similar_companies:
        print(f"- {c.name} (Score: {score:.4f})")

if __name__ == "__main__":
    asyncio.run(main())

# TODO: check
