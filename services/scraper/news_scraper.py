import feedparser
import httpx
import structlog
from typing import List
from datetime import datetime, timezone
from urllib.parse import quote_plus
from schemas.company import NewsItem

logger = structlog.get_logger()

class NewsScraper:
    def __init__(self):
        self.base_url = "https://news.google.com/rss/search?q="
        self.client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)

    async def close(self):
        """Close the underlying httpx client."""
        await self.client.aclose()

    async def scrape_news(self, company_name: str) -> List[NewsItem]:        
        query = quote_plus(company_name)
        url = f"{self.base_url}{query}"
        
        logger.info("scraping_news", company=company_name, url=url)
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            xml_content = response.text
        except httpx.HTTPError as e:
            logger.error("news_fetch_failed", url=url, error=str(e))
            return []

        feed = feedparser.parse(xml_content)
        news_items = []
        
        for entry in feed.entries[:10]:  # Limit to 10 items
            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    # feedparser returns time.struct_time, convert to datetime
                    published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                except Exception as e:
                    logger.warning("invalid_publish_date", error=str(e))
            
            item = NewsItem(
                title=entry.title,
                summary=entry.summary if hasattr(entry, "summary") else None,
                url=entry.link,
                published_at=published_at
            )
            news_items.append(item)
            
        return news_items
