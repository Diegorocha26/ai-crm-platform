import structlog
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from services.scraper.base_scraper import BaseScraper
from schemas.company import RawCompanyData

logger = structlog.get_logger()

TECH_KEYWORDS = {
    "React": ["react", "react.js"],
    "Vue": ["vue", "vue.js"],
    "Angular": ["angular", "angular.js"],
    "Next.js": ["next.js", "__next"],
    "Nuxt": ["nuxt"],
    "AWS": ["aws", "amazon web services"],
    "Stripe": ["stripe"],
    "Tailwind": ["tailwind", "tailwindcss"],
    "Bootstrap": ["bootstrap"],
    "Shopify": ["shopify"],
    "WordPress": ["wordpress", "wp-content"],
    "Django": ["django"],
    "Flask": ["flask"],
    "FastAPI": ["fastapi"],
    "Node.js": ["node.js", "nodejs"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Docker": ["docker"],
}

class WebsiteScraper(BaseScraper):
    async def scrape(self, url: str) -> RawCompanyData:
        logger.info("scraping_website", url=url)

        try:
            html = await self._fetch_html(url)

            if len(html) < 500: # Heuristic: if content is too short, might need JS
                 logger.info("content_too_short_switching_to_playwright", url=url, length=len(html))
                 html = await self._fetch_with_js(url)

        except Exception as e:
            logger.info("httpx_failed_retrying_playwright", url=url, error=str(e))
            html = await self._fetch_with_js(url)
            
        soup = BeautifulSoup(html, "html.parser")
        
        name = self._extract_company_name(soup)
        description = self._extract_description(soup)
        tech_stack = self._detect_tech_stack(html)
        social_links = self._extract_links(soup)
        
        # Truncate raw_html to a reasonable size to prevent massive DB records
        truncated_html = html[:100000] 

        return RawCompanyData(
            name=name,
            website=url,
            description=description,
            raw_html=truncated_html,
            detected_tech=tech_stack,
            social_links=social_links,
            source="website"
        )
    
    def _extract_company_name(self, soup: BeautifulSoup) -> Optional[str]:
        # 1. Try OpenGraph site name
        og_site_name = soup.find("meta", property="og:site_name")
        if og_site_name and og_site_name.get("content"):
            return og_site_name["content"]
        
        # 2. Try Title tag, taking first part before separator
        if soup.title and soup.title.string:
            title_text = soup.title.string.strip()
            separators = ["|", "-", "—", ":"]
            for sep in separators:
                if sep in title_text:
                    return title_text.split(sep)[0].strip()
            return title_text
            
        # 3. Try H1
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
            
        return None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        # 1. Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            return meta_desc["content"]
            
        # 2. OG description
        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            return og_desc["content"]
            
        return None

    def _detect_tech_stack(self, html: str) -> List[str]:
        detected = set()
        html_lower = html.lower()
        for tech, keywords in TECH_KEYWORDS.items():
            for kw in keywords:
                if kw in html_lower:
                    detected.add(tech)
                    break
        return list(detected)

    def _extract_links(self, soup: BeautifulSoup) -> Dict[str, str]:
        links = {}
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            if "linkedin.com/company" in href:
                links.setdefault("linkedin", a["href"])
            elif "twitter.com" in href or "x.com" in href:
                links.setdefault("twitter", a["href"])
            elif "github.com" in href:
                links.setdefault("github", a["href"])
            elif "facebook.com" in href:
                links.setdefault("facebook", a["href"])
            elif "instagram.com" in href:
                links.setdefault("instagram", a["href"])
        return links
