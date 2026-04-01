import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from services.llm.client import LLMClient
from services.rag.retriever import Retriever
from core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    Provides common infrastructure for LLM calls, RAG retrieval, and DB access.
    """
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        retriever: Optional[Retriever] = None,
    ):
        self.llm = llm_client or LLMClient()
        self.retriever = retriever or Retriever()
        self.db_session_factory = AsyncSessionLocal

    @abstractmethod
    async def run(self, task: Dict[str, Any]) -> Any:
        """
        Execute the main logic of the agent.
        Each subclass must implement this method.
        """
        pass

    def _log_info(self, message: str, **kwargs):
        """Standardized info logging for agents."""
        logger.info(f"[{self.__class__.__name__}] {message}", extra=kwargs)

    def _log_error(self, message: str, **kwargs):
        """Standardized error logging for agents."""
        logger.error(f"[{self.__class__.__name__}] {message}", extra=kwargs)
