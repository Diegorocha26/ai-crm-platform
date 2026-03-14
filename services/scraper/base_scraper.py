from abc import ABC, abstractmethod
import httpx
from playwright.async_api import async_playwright
from schemas.company import RawCompanyData
import structlog

logger = structlog.get_logger()

class BaseScraper(ABC):
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)
        self.playwright = None
        self.browser = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        await self.client.aclose()

    @abstractmethod
    async def scrape(self, url: str) -> RawCompanyData:
        """Scrape a URL and return raw structured data."""
        pass
    
    async def _fetch_html(self, url: str) -> str:
        """Fetch HTML using httpx with timeout and retry."""
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            logger.error("fetch_html_failed", url=url, error=str(e))
            raise

    async def _fetch_with_js(self, url: str) -> str:
        """Fetch JS-rendered HTML using Playwright."""
        page = await self.browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            content = await page.content()
            return content
        except Exception as e:
            logger.error("fetch_with_js_failed", url=url, error=str(e))
            raise
        finally:
            await page.close()
