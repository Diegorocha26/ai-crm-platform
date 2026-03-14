import asyncio
import argparse
import structlog
from services.scraper.website_scraper import WebsiteScraper
from services.scraper.news_scraper import NewsScraper

# Configure structlog to print to stderr
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

async def main():
    parser = argparse.ArgumentParser(description="Test scraper service")
    parser.add_argument("--url", help="Company website URL to scrape")
    parser.add_argument("--news", help="Company name to scrape news for")
    
    args = parser.parse_args()
    
    if args.url:
        print(f"\n--- Scraping Website: {args.url} ---\n")
        scraper = WebsiteScraper()
        await scraper.start()
        try:
            data = await scraper.scrape(args.url)
            print(f"Name: {data.name}")
            print(f"Description: {data.description}")
            print(f"Tech Stack: {data.detected_tech}")
            print(f"Socials: {data.social_links}")
            print(f"Raw HTML Size: {len(data.raw_html)} bytes")
        except Exception as e:
            print(f"Error scraping website: {e}")
        finally:
            await scraper.close()

    if args.news:
        print(f"\n--- Scraping News: {args.news} ---\n")
        news_scraper = NewsScraper()
        try:
            items = await news_scraper.scrape_news(args.news)
            for i, item in enumerate(items, 1):
                print(f"{i}. {item.title} ({item.published_at})")
                print(f"   {item.url}")
        except Exception as e:
            print(f"Error scraping news: {e}")
        finally:
            await news_scraper.close()

    if not args.url and not args.news:
        print("Please provide --url or --news argument")

if __name__ == "__main__":
    asyncio.run(main())
