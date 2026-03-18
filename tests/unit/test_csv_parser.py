from services.ingestion.csv_parser import parse_csv

def test_parse_valid_csv():
    csv_content = b"website,name\nexample.com,Example Co\nhttps://google.com,Google"
    companies, errors = parse_csv(csv_content)
    
    assert len(companies) == 2
    assert len(errors) == 0
    assert str(companies[0].website) == "https://example.com/"
    assert companies[1].name == "Google"

def test_parse_invalid_csv():
    # Row 1: Invalid URL (Pydantic strictly checks HttpUrl)
    # Row 2: Missing website (empty)
    csv_content = b"website,name\nnot a url,Bad Co\n,No Website"
    companies, errors = parse_csv(csv_content)
    
    assert len(companies) == 0
    assert len(errors) == 2
    
    # Check row numbers (1-based index from enumerate)
    assert errors[0]["row"] == 1
    assert errors[1]["row"] == 2
