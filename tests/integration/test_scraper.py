import pytest
import pytest_asyncio
from services.scraper.website_scraper import WebsiteScraper
from services.scraper.news_scraper import NewsScraper

@pytest_asyncio.fixture
async def website_scraper():
    scraper = WebsiteScraper()
    await scraper.start()
    yield scraper
    await scraper.close()

@pytest_asyncio.fixture
async def news_scraper():
    scraper = NewsScraper()
    yield scraper
    await scraper.close()

@pytest.mark.integration
async def test_website_scraper_stripe(website_scraper):
    url = "https://stripe.com"
    data = await website_scraper.scrape(url)

    assert str(data.website).startswith(url)
    assert data.name is not None
    assert "Stripe" in data.name
    assert len(data.raw_html) > 500
    assert data.scraped_at is not None
    assert isinstance(data.detected_tech, list)
    print(data.model_dump())

@pytest.mark.integration
async def test_news_scraper_google(news_scraper):
    items = await news_scraper.scrape_news("Google")
    
    assert isinstance(items, list)
    # News results vary, but usually Google has news.
    # We just check the structure if items exist.
    if items:
        assert all(item.title and item.url for item in items)

    for item in items[:2]:
        print(item.model_dump())
