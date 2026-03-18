from schemas.company import RawCompanyData, CompanyCreate

def normalize_company(raw: RawCompanyData) -> CompanyCreate:
    """
    Normalize raw scraped data into a company creation schema.
    Applies truncation and data cleaning rules.
    """
    description = raw.description
    if description and len(description) > 5000:
        description = description[:5000]

    return CompanyCreate(
        website=raw.website,
        name=raw.name,
        description=description,
        raw_html=raw.raw_html,
        source_url=str(raw.website),
        tech_stack=raw.detected_tech,
        social_links=raw.social_links
    )

def normalize_csv_row(row: dict) -> CompanyCreate:
    """
    Normalize a CSV row dict to CompanyCreate schema.
    Handles basic URL correction.
    """
    website = row.get("website", "").strip()
    
    # Simple heuristic to fix missing protocol
    if website and not website.startswith(("http://", "https://")):
        website = f"https://{website}"
        
    # Map other fields if present
    name = row.get("name")
    if isinstance(name, str):
        name = name.strip()
        
    description = row.get("description")
    if isinstance(description, str):
        description = description.strip()

    return CompanyCreate(
        website=website,
        name=name,
        description=description,
        # Other fields are optional in CSV usually
    )
