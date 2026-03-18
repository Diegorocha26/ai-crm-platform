import pytest
from pydantic import ValidationError
from schemas.company import RawCompanyData
from services.ingestion.normalizer import normalize_company, normalize_csv_row

def test_normalize_company():
    raw = RawCompanyData(
        website="https://example.com",
        raw_html="<html></html>",
        name="Example Inc.",
        description="A" * 6000 # Long description
    )
    
    normalized = normalize_company(raw)
    
    assert str(normalized.website) == "https://example.com/"
    assert len(normalized.description) == 5000
    assert normalized.tech_stack == []

def test_normalize_csv_row():
    row = {
        "website": "example.com", # Missing protocol
        "name": " Example Co ",
        "description": "Desc"
    }
    
    normalized = normalize_csv_row(row)
    
    # Pydantic HttpUrl normalizes to string with protocol
    assert str(normalized.website) == "https://example.com/"
    assert normalized.name == "Example Co"

def test_normalize_csv_row_validation_error():
    row = {"name": "No Website"}
    # normalize_csv_row will try to create CompanyCreate with empty website string if not present
    # CompanyCreate.website expects HttpUrl, which fails on empty string
    with pytest.raises(ValidationError):
        normalize_csv_row(row)
