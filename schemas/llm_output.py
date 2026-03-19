from typing import Literal
from pydantic import BaseModel, Field

class CompanySummaryOutput(BaseModel):
    industry: str | None = None
    business_model: Literal["B2B", "B2C", "B2B2C", "marketplace", "other"] = "other"
    target_customer: str | None = None
    product_description: str | None = None
    tech_stack: list[str] = Field(default_factory=list)
    growth_signals: list[str] = Field(default_factory=list)
    company_stage: Literal["startup", "growth", "enterprise", "unknown"] = "unknown"

class LeadScoreOutput(BaseModel):
    score: float = Field(ge=1, le=10, description="Score from 1 to 10")
    reasoning: str
    key_factors: list[str] = Field(default_factory=list)
    recommended_action: str

class OutreachOutput(BaseModel):
    subject: str
    body: str
    tone: str
    personalization_hooks: list[str] = Field(default_factory=list)
