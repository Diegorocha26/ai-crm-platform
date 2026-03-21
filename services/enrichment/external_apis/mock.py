from schemas.enrichment import EmailResult
from .base import BaseEnrichmentProvider

class MockEnrichmentProvider(BaseEnrichmentProvider):
    async def find_emails(self, domain: str) -> list[EmailResult]:
        """Return deterministic mock emails."""
        return [
            EmailResult(
                email=f"contact@{domain}",
                confidence=90,
                type="generic",
                source="mock"
            ),
            EmailResult(
                email=f"ceo@{domain}",
                confidence=50,
                type="personal",
                source="mock"
            )
        ]
