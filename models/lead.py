from __future__ import annotations
import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, Enum, ForeignKey, Float, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base
from models.company import EnrichmentStatus

if TYPE_CHECKING:
    from models.company import Company
    from models.generated_content import GeneratedContent

class SeniorityLevel(enum.Enum):
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    DIRECTOR = "director"
    VP = "vp"
    CXO = "cxo"
    UNKNOWN = "unknown"

class Lead(Base):
    """
    Model representing an individual lead or contact person.
    Associated with a specific Company and contains AI-driven relevance scores.
    """
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(1024))
    
    role: Mapped[str | None] = mapped_column(String(255))
    seniority: Mapped[SeniorityLevel] = mapped_column(
        Enum(SeniorityLevel), 
        default=SeniorityLevel.UNKNOWN,
        server_default="unknown"
    )
    department: Mapped[str | None] = mapped_column(String(100))
    
    # AI Enrichment & Scoring
    buying_power_score: Mapped[float | None] = mapped_column(Float)
    relevance_score: Mapped[float | None] = mapped_column(Float)
    
    enrichment_status: Mapped[EnrichmentStatus] = mapped_column(
        Enum(EnrichmentStatus), 
        default=EnrichmentStatus.PENDING,
        server_default="pending"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

    # Relationships
    company: Mapped[Company] = relationship("Company", back_populates="leads")
    generated_contents: Mapped[list[GeneratedContent]] = relationship("GeneratedContent", back_populates="lead", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Lead(full_name={self.full_name}, email={self.email})>"
