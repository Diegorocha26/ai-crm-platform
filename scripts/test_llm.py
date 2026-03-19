import asyncio
from unittest.mock import AsyncMock, MagicMock
from services.llm.client import LLMClient

async def test_llm_flow():
    print("Testing LLM Client Flow (Mocked OpenAI)...")
    
    # Mocking OpenAI client injection
    client = LLMClient()
    
    # Create a mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = """
    {
        "industry": "Fintech",
        "business_model": "B2B",
        "target_customer": "Developers",
        "product_description": "Payments infrastructure.",
        "tech_stack": ["Ruby", "Go"],
        "growth_signals": ["IPO rumors"],
        "company_stage": "enterprise"
    }
    """
    mock_response.usage.total_tokens = 100
    
    # Mock the completions.create method
    # Even if client.client is None (no key), we replace it with Mock
    client.client = AsyncMock()
    client.client.chat.completions.create.return_value = mock_response
    
    print("  Invoking complete()...")
    # We pass entity_id to trigger the optional DB log path (which should just log error if no DB)
    result = await client.complete(
        prompt_name="company_summary",
        variables={"website_content": "Stripe content placeholder"},
        entity_id="test-entity-1",
        entity_type="company"
    )
    
    print("  Result parsed successfully:")
    print(result)
    assert result.industry == "Fintech"
    print("✅ LLM Client Flow Test Passed!")

if __name__ == "__main__":
    asyncio.run(test_llm_flow())
