from __future__ import annotations
import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, JSON, DateTime, Enum, Text, func
from sqlalchemy.dialects.mysql import MEDIUMTEXT, CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base

if TYPE_CHECKING:
    from models.lead import Lead

class EnrichmentStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"

class Company(Base):
    """
    Model representing a company entity within the CRM platform.
    Stores both raw scraped data and AI-enriched intelligence.
    """
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    industry: Mapped[str | None] = mapped_column(String(100), index=True)
    business_model: Mapped[str | None] = mapped_column(String(50)) # e.g., B2B, B2C
    target_customer: Mapped[str | None] = mapped_column(Text)
    
    # Store dynamic JSON data
    tech_stack: Mapped[dict | list | None] = mapped_column(JSON)
    growth_signals: Mapped[dict | list | None] = mapped_column(JSON)
    social_links: Mapped[dict | None] = mapped_column(JSON)
    
    # Updated to String for ranges (e.g., "51-200")
    employee_count: Mapped[str | None] = mapped_column(String(50))
    
    source_url: Mapped[str | None] = mapped_column(String(1024))
    
    # Updated to MEDIUMTEXT for large HTML content
    raw_html: Mapped[str | None] = mapped_column(MEDIUMTEXT)
    
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
    leads: Mapped[list[Lead]] = relationship("Lead", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Company(name={self.name}, website={self.website})>"
