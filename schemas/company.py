from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime, timezone
from typing import List, Dict, Optional, Literal

class RawCompanyData(BaseModel):
    name: Optional[str] = None
    website: HttpUrl
    description: Optional[str] = None
    raw_html: str
    detected_tech: List[str] = Field(default_factory=list)
    social_links: Dict[str, str] = Field(default_factory=dict)
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: Literal["website", "news", "manual"] = "website"

class NewsItem(BaseModel):
    title: str
    summary: Optional[str] = None
    url: HttpUrl
    published_at: Optional[datetime] = None
