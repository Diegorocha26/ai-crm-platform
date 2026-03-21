from pydantic import BaseModel, EmailStr
from typing import Optional, Literal

class EmailResult(BaseModel):
    """Schema for email enrichment results."""
    email: EmailStr
    confidence: Optional[int] = None
    type: Optional[Literal["personal", "generic"]] = None
    source: str  # e.g., "hunter", "mock", "in-house"
