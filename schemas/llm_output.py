from typing import Literal
from pydantic import BaseModel, Field, field_validator

class CompanySummaryOutput(BaseModel):
    industry: str | None = None
    business_model: Literal["B2B", "B2C", "B2B2C", "marketplace", "other"] = "other"
    target_customer: str | None = None
    product_description: str | None = None
    tech_stack: list[str] = Field(default_factory=list)
    growth_signals: list[str] = Field(default_factory=list)
    company_stage: Literal["startup", "growth", "enterprise", "unknown"] = "unknown"

    @field_validator("business_model", mode="before")
    @classmethod
    def validate_business_model(cls, v):
        if v is None:
            return "other"
        return v

    @field_validator("company_stage", mode="before")
    @classmethod
    def validate_company_stage(cls, v):
        if v is None:
            return "unknown"
        return v

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
