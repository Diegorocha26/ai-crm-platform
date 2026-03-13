from __future__ import annotations
import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base

if TYPE_CHECKING:
    from models.lead import Lead

class ContentType(enum.Enum):
    OUTREACH_EMAIL = "outreach_email"
    SUMMARY = "summary"
    TALKING_POINTS = "talking_points"

class GeneratedContent(Base):
    """
    Stores final output content generated for leads (e.g., outreach emails).
    Each piece of content is linked to a lead and tracks the model/prompt version used.
    """
    __tablename__ = "generated_content"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)
    
    # outreach_email, summary, talking_points, etc.
    content_type: Mapped[ContentType] = mapped_column(Enum(ContentType))
    
    content: Mapped[str] = mapped_column(Text)
    
    prompt_version: Mapped[str] = mapped_column(String(50))
    model_used: Mapped[str] = mapped_column(String(100))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        server_default=func.now()
    )

    # Relationship to Lead
    lead: Mapped[Lead] = relationship("Lead", back_populates="generated_contents")

    def __repr__(self) -> str:
        return f"<GeneratedContent(lead_id={self.lead_id}, type={self.content_type})>"
