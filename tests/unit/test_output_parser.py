import pytest
from services.llm.output_parser import OutputParser, LLMOutputParseError
from schemas.llm_output import CompanySummaryOutput, OutreachOutput

def test_parse_company_summary_valid():
    parser = OutputParser()
    raw = """
    {
        "industry": "SaaS",
        "business_model": "B2B",
        "target_customer": "Startups",
        "product_description": "A CRM platform.",
        "tech_stack": ["Python", "React"],
        "growth_signals": ["hiring"],
        "company_stage": "startup"
    }
    """
    result = parser.parse_company_summary(raw)
    
    # Assert full schema integrity
    assert isinstance(result, CompanySummaryOutput)
    assert result.industry == "SaaS"
    assert result.business_model == "B2B"
    assert result.target_customer == "Startups"
    assert "Python" in result.tech_stack
    assert result.company_stage == "startup"

def test_parse_company_summary_repair():
    parser = OutputParser()
    # Missing quotes around keys, single quotes for values, trailing comma
    raw = """
    {
        industry: 'SaaS',
        business_model: 'B2B',
        tech_stack: ['Python', 'React'],
    }
    """
    result = parser.parse_company_summary(raw)
    assert result.industry == "SaaS"
    assert len(result.tech_stack) == 2

def test_parse_lead_score_schema_error():
    parser = OutputParser()
    # Score out of range (11) - this should trigger a ValidationError
    raw = """
    {
        "score": 11,
        "reasoning": "Too good",
        "key_factors": [],
        "recommended_action": "reach_out"
    }
    """
    with pytest.raises(LLMOutputParseError) as excinfo:
        parser.parse_lead_score(raw)
    
    # Assert exception attributes instead of message string
    assert excinfo.value.raw_output == raw
    assert excinfo.value.errors is not None
    assert any(err["loc"] == ("score",) for err in excinfo.value.errors)

def test_parse_outreach_valid():
    parser = OutputParser()
    raw = """
    {
        "subject": "Hello",
        "body": "World",
        "tone": "casual",
        "personalization_hooks": ["hook1"]
    }
    """
    result = parser.parse_outreach(raw)
    assert isinstance(result, OutreachOutput)
    assert result.subject == "Hello"
    assert result.tone == "casual"

def test_parse_malformed_unrepairable():
    parser = OutputParser()
    # Even if json_repair returns {}, LeadScoreOutput has required fields (score, reasoning, etc)
    # so it should still fail validation.
    raw = "!!! Not even close to JSON !!!"
    
    with pytest.raises(LLMOutputParseError) as excinfo:
        parser.parse_lead_score(raw)
    
    # Check that we captured the raw junk
    assert excinfo.value.raw_output == raw
