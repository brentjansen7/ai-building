import asyncio
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

logger = structlog.get_logger()


class BaseScraper(ABC):
    """Base class voor alle vastgoed scrapers."""

    HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]

    def __init__(self, proxy_list: Optional[List[str]] = None):
        self.proxy_list = proxy_list or []
        self.proxy_idx = 0
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self.playwright = None

    def _get_proxy(self) -> Optional[Dict]:
        if not self.proxy_list:
            return None
        proxy_url = self.proxy_list[self.proxy_idx % len(self.proxy_list)]
        self.proxy_idx += 1
        # Playwright proxy format: {"server": "http://proxy:8080", "username": ..., "password": ...}
        return {"server": proxy_url}

    def _get_user_agent(self) -> str:
        return random.choice(self.USER_AGENTS)

    async def init(self):
        """Start Playwright browser."""
        self.playwright = await async_playwright().start()
        proxy = self._get_proxy()
        self._browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        self._context = await self._browser.new_context(
            user_agent=self._get_user_agent(),
            proxy=proxy,
            viewport={"width": 1280, "height": 720},
            locale="nl-NL",
            extra_http_headers=self.HEADERS,
        )
        # Verberg webdriver flag
        await self._context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        logger.info("Browser gestart", scraper=self.__class__.__name__)

    async def close(self):
        """Sluit browser."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def _new_page(self) -> Page:
        """Maak nieuwe pagina."""
        return await self._context.new_page()

    async def _random_delay(self, min_s: float = 2.0, max_s: float = 6.0):
        """Random delay om rate limiting te vermijden."""
        delay = random.uniform(min_s, max_s)
        await asyncio.sleep(delay)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=3, max=15),
        reraise=True,
    )
    async def _fetch_page(self, url: str, wait_for: Optional[str] = None) -> Page:
        """Haal pagina op met retry logica."""
        page = await self._new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            if wait_for:
                await page.wait_for_selector(wait_for, timeout=10000)
            await self._random_delay(1.0, 3.0)
            return page
        except Exception as e:
            await page.close()
            logger.warning("Pagina fout", url=url, error=str(e))
            raise

    def _parse_price(self, text: Optional[str]) -> Optional[int]:
        """Parse prijs tekst naar integer."""
        if not text:
            return None
        import re
        digits = re.sub(r"[^\d]", "", text)
        return int(digits) if digits else None

    def _parse_sqm(self, text: Optional[str]) -> Optional[int]:
        """Parse m² tekst naar integer."""
        if not text:
            return None
        import re
        match = re.search(r"(\d+)", text.replace(".", ""))
        return int(match.group(1)) if match else None

    @abstractmethod
    async def get_listing_urls(self, search_term: str = "", max_pages: int = 5) -> List[str]:
        """Haal alle listing URLs op."""
        pass

    @abstractmethod
    async def parse_listing(self, url: str) -> Optional[Dict]:
        """Parse één listing pagina."""
        pass

    async def scrape_all(self, search_term: str = "kluswoning", max_pages: int = 10) -> List[Dict]:
        """Scrape alle listings."""
        await self.init()
        listings = []
        try:
            urls = await self.get_listing_urls(search_term, max_pages)
            logger.info("URLs gevonden", count=len(urls), scraper=self.__class__.__name__)

            for i, url in enumerate(urls):
                try:
                    listing = await self.parse_listing(url)
                    if listing:
                        listings.append(listing)
                    await self._random_delay(2.0, 5.0)
                except Exception as e:
                    logger.error("Listing parse fout", url=url, error=str(e))
                    continue

            logger.info("Scrape klaar", total=len(listings), scraper=self.__class__.__name__)
        finally:
            await self.close()

        return listings
