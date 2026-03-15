import csv
from io import StringIO
from typing import List, Tuple, Dict, Any
from pydantic import ValidationError
from schemas.company import CompanyCreate
from services.ingestion.normalizer import normalize_csv_row

def parse_csv(file_bytes: bytes) -> Tuple[List[CompanyCreate], List[Dict[str, Any]]]:
    """
    Parse a CSV file content and return valid CompanyCreate objects and errors.
    
    Args:
        file_bytes: The raw content of the CSV file.
        
    Returns:
        Tuple containing:
        - List of valid CompanyCreate objects
        - List of error dictionaries: {"row": int, "error": str, "data": dict}
    """
    valid_companies = []
    errors = []
    
    # Attempt to decode
    try:
        content = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            content = file_bytes.decode("latin-1")
        except UnicodeDecodeError:
            return [], [{"row": 0, "error": "Unable to decode file. Please use UTF-8 or Latin-1."}]
            
    # Parse CSV
    with StringIO(content) as f:
        reader = csv.DictReader(f)
    
    if not reader.fieldnames:
        return [], [{"row": 0, "error": "Empty CSV file or missing headers."}]
        
    # Check for required column 
    # TODO: (case-insensitive check could be better but let's stick to 'website')
    headers = [h.strip().lower() for h in reader.fieldnames if h]
    if "website" not in headers:
        return [], [{"row": 0, "error": "Missing required column: 'website'"}]

    for i, row in enumerate(reader, start=1):
        # Clean row keys and values
        clean_row = {}
        for k, v in row.items():
            if k:
                clean_row[k.strip().lower()] = v.strip() if v else ""
        
        try:
            company = normalize_csv_row(clean_row)
            valid_companies.append(company)
        except ValidationError as e:
            # Extract first error message for brevity
            msg = e.errors()[0]["msg"] if e.errors() else str(e)
            errors.append({"row": i, "error": msg, "data": clean_row})
        except Exception as e:
            errors.append({"row": i, "error": str(e), "data": clean_row})
            
    return valid_companies, errors
