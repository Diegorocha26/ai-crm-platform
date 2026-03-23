from abc import ABC, abstractmethod
from schemas.enrichment import EmailResult

class BaseEnrichmentProvider(ABC):
    @abstractmethod
    async def find_emails(self, domain: str) -> list[EmailResult]:
        """Find emails for a given domain."""
        pass
