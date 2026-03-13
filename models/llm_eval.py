import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Enum, ForeignKey, Float, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base

class EvalType(enum.Enum):
    LLM_JUDGE = "llm_judge"
    RULE_BASED = "rule_based"
    HUMAN = "human"

class LLMEval(Base):
    """
    Stores evaluation results for specific enrichments.
    Allows comparing different prompt versions or evaluator models (LLM-as-judge).
    """
    __tablename__ = "llm_evals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Link to the specific enrichment being evaluated
    enrichment_id: Mapped[int] = mapped_column(ForeignKey("enrichments.id", ondelete="CASCADE"), index=True)
    
    # llm_judge, rule_based, manual_human, etc.
    eval_type: Mapped[EvalType] = mapped_column(Enum(EvalType))
    
    score: Mapped[float] = mapped_column(Float)
    rubric: Mapped[dict | None] = mapped_column(JSON)
    
    evaluator_model: Mapped[str | None] = mapped_column(String(100))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<LLMEval(enrichment_id={self.enrichment_id}, score={self.score})>"
