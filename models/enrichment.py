import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Enum, JSON, Integer, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base

class EntityType(enum.Enum):
    COMPANY = "company"
    LEAD = "lead"

class EnrichmentType(enum.Enum):
    SUMMARY = "summary"
    SCORING = "scoring"
    RAG = "rag"
    OUTREACH = "outreach"
    OTHER = "other"

class Enrichment(Base):
    """
    Audit log for LLM operations.
    Stores raw inputs, outputs, costs, and performance metrics.
    """
    __tablename__ = "enrichments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Generic reference to the entity being enriched
    entity_id: Mapped[str] = mapped_column(CHAR(36), index=True)
    entity_type: Mapped[EntityType] = mapped_column(Enum(EntityType))
    
    enrichment_type: Mapped[EnrichmentType] = mapped_column(Enum(EnrichmentType))
    prompt_version: Mapped[str] = mapped_column(String(50))
    
    # AI Data
    raw_llm_output: Mapped[dict | None] = mapped_column(JSON)
    parsed_output: Mapped[dict | None] = mapped_column(JSON)
    
    # Performance & Cost Monitoring
    model_used: Mapped[str] = mapped_column(String(100))
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True, 
        server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<Enrichment(entity_type={self.entity_type}, type={self.enrichment_type})>"
