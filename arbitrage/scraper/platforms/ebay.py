"""
eBay scraper — dual approach:

1. Official Finding API (active listings, 5000 calls/day free)
   → Used for monitoring current prices

2. Completed/Sold listings scrape (no official API for sold data)
   → Most valuable for price reference: real transaction prices
   → Lightweight HTML scrape, soft rate limiting

eBay sold data is the best price reference in the system.
"""

import logging
import os
import re
from typing import List, Optional
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from scraper.base import BaseScraper

logger = logging.getLogger(__name__)

EBAY_FINDING_API = "https://svcs.ebay.com/services/search/FindingService/v1"
EBAY_APP_ID = os.getenv("EBAY_APP_ID", "")  # Free from developer.ebay.com

# Search keywords for high-value arbitrage categories
SEARCH_TERMS = [
    "sony camera", "canon lens", "nikon dslr",
    "iphone 13 14 15", "macbook pro",
    "rolex", "omega speedmaster",
    "vintage hifi", "marantz", "pioneer receiver",
    "gaming laptop", "rtx 4070 4080",
    "dyson", "thermomix",
    "leica camera", "hasselblad",
    "ps5 playstation", "nintendo switch",
]


class EbaySoldScraper:
    """
    Scrape eBay completed/sold listings for price history data.
    This is the primary source of real transaction prices.
    """

    def __init__(self):
        self.session = httpx.AsyncClient(
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "nl-NL,nl;q=0.9",
            },
            follow_redirects=True,
        )

    async def fetch_sold_listings(
        self,
        keyword: str,
        max_pages: int = 2,
    ) -> List[dict]:
        """
        Fetch recently sold eBay listings for a keyword.
        Used to populate sold_listings table for price estimation.
        """
        all_sold = []

        for page in range(1, max_pages + 1):
            params = {
                "_nkw": keyword,
                "LH_Sold": "1",
                "LH_Complete": "1",
                "_sop": "13",  # Sort by newest first
                "_ipg": "50",  # 50 per page
                "_pgn": str(page),
            }

            try:
                import asyncio
                await asyncio.sleep(2)  # Polite delay

                resp = await self.session.get(
                    "https://www.ebay.nl/sch/i.html",
                    params=params,
                )
                resp.raise_for_status()

                items = self._parse_sold_html(resp.text, keyword)
                all_sold.extend(items)

                logger.debug(f"[ebay_sold] '{keyword}' page {page}: {len(items)} results")

                if not items:
                    break

            except Exception as e:
                logger.warning(f"[ebay_sold] '{keyword}' page {page} failed: {e}")
                break

        return all_sold

    def _parse_sold_html(self, html: str, keyword: str) -> List[dict]:
        """Parse eBay search results HTML to extract sold listings."""
        soup = BeautifulSoup(html, "lxml")
        results = []

        items = soup.select(".s-item")
        for item in items:
            try:
                # Skip "More items like this" placeholder
                if item.select_one(".s-item__title--tagblock"):
                    continue

                title_el = item.select_one(".s-item__title")
                price_el = item.select_one(".s-item__price")
                sold_el = item.select_one(".POSITIVE, .s-item__caption--signal")
                image_el = item.select_one(".s-item__image-img")
                link_el = item.select_one("a.s-item__link")
                item_id_match = re.search(r"/(\d{10,})", link_el["href"]) if link_el else None

                if not title_el or not price_el:
                    continue

                title = title_el.get_text(strip=True)
                price_text = price_el.get_text(strip=True)
                price = self._parse_price(price_text)

                if price <= 0 or title in ("Shop on eBay",):
                    continue

                results.append({
                    "platform": "ebay",
                    "external_id": item_id_match.group(1) if item_id_match else f"ebay_{hash(title+price_text)}",
                    "title": title,
                    "sold_price": price,
                    "condition": None,
                    "category": keyword,  # Use keyword as category proxy
                    "brand": None,
                    "sold_at": datetime.now(timezone.utc),
                    "image_url": image_el.get("src", "") if image_el else "",
                    "url": link_el["href"] if link_el else "",
                })

            except Exception as e:
                logger.debug(f"[ebay_sold] Parse error: {e}")
                continue

        return results

    @staticmethod
    def _parse_price(text: str) -> float:
        """Extract price from eBay price text (handles ranges, currencies)."""
        # Handle price range: take the higher price (completed sale)
        nums = re.findall(r"[\d.]+", text.replace(",", "."))
        if nums:
            return max(float(n) for n in nums if float(n) > 0)
        return 0.0

    async def close(self):
        await self.session.aclose()


class EbayFindingAPIScraper(BaseScraper):
    """
    eBay Finding API — official, free, 5000 calls/day.
    Used to monitor current active listings.
    Register at developer.ebay.com for a free AppID.
    """

    @property
    def platform(self) -> str:
        return "ebay"

    @property
    def requests_per_minute(self) -> int:
        return 60  # Official API, generous limits

    async def fetch_listings(self) -> List[dict]:
        """Fetch active listings across target search terms."""
        if not EBAY_APP_ID:
            logger.warning("[ebay] EBAY_APP_ID not set — skipping Finding API scrape")
            return []

        all_listings = []

        for keyword in SEARCH_TERMS[:10]:  # Limit to avoid burning daily quota
            try:
                listings = await self._search_keyword(keyword)
                all_listings.extend(listings)
            except Exception as e:
                logger.error(f"[ebay] Keyword '{keyword}' failed: {e}")
                continue

        return all_listings

    async def _search_keyword(self, keyword: str) -> List[dict]:
        """Search eBay for active listings matching a keyword."""
        params = {
            "OPERATION-NAME": "findItemsByKeywords",
            "SERVICE-VERSION": "1.0.0",
            "SECURITY-APPNAME": EBAY_APP_ID,
            "RESPONSE-DATA-FORMAT": "JSON",
            "keywords": keyword,
            "paginationInput.entriesPerPage": "50",
            "itemFilter(0).name": "ListingType",
            "itemFilter(0).value": "FixedPrice",
            "itemFilter(1).name": "Condition",
            "itemFilter(1).value": "Used",
            "sortOrder": "StartTimeNewest",
        }

        try:
            response = await self.get(EBAY_FINDING_API, params=params)
            data = response.json()

            search_result = (
                data.get("findItemsByKeywordsResponse", [{}])[0]
                   .get("searchResult", [{}])[0]
                   .get("item", [])
            )

            listings = []
            for item in search_result:
                listing = self._parse_finding_item(item, keyword)
                if listing:
                    listings.append(listing)

            return listings

        except Exception as e:
            logger.warning(f"[ebay] Finding API search for '{keyword}' failed: {e}")
            return []

    def _parse_finding_item(self, item: dict, keyword: str) -> dict | None:
        """Parse a Finding API item into normalized format."""
        try:
            price_info = item.get("sellingStatus", [{}])[0]
            current_price = price_info.get("currentPrice", [{}])[0]
            price = float(current_price.get("__value__", 0))

            if price <= 0:
                return None

            gallery_url = item.get("galleryURL", [""])[0]
            item_url = item.get("viewItemURL", [""])[0]
            title = item.get("title", [""])[0]
            condition = item.get("condition", [{}])[0].get("conditionDisplayName", [""])[0]
            item_id = item.get("itemId", [""])[0]
            location = item.get("location", [""])[0]

            return {
                "platform": self.platform,
                "external_id": str(item_id),
                "title": title,
                "description": "",
                "price": price,
                "condition": self.normalize_condition(condition),
                "category": keyword,
                "brand": None,
                "seller_id": item.get("sellerId", [{}])[0].get("userId", [""])[0] if "sellerId" in item else None,
                "location": location,
                "url": item_url,
                "image_urls": [gallery_url] if gallery_url else [],
                "posted_at": None,
                "metadata": {
                    "listing_type": item.get("listingInfo", [{}])[0].get("listingType", [""])[0],
                },
            }
        except Exception as e:
            logger.debug(f"[ebay] Parse error: {e}")
            return None


async def import_ebay_sold_data(keywords: Optional[List[str]] = None) -> int:
    """
    Import eBay sold listings into sold_listings table.
    Run this once daily or weekly to populate price reference data.

    Returns total number of sold listings imported.
    """
    from db.database import get_session
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from db.models import SoldListing

    if not keywords:
        keywords = SEARCH_TERMS

    scraper = EbaySoldScraper()
    total = 0

    try:
        for keyword in keywords:
            sold = await scraper.fetch_sold_listings(keyword, max_pages=3)

            if not sold:
                continue

            async with get_session() as session:
                for item in sold:
                    stmt = pg_insert(SoldListing).values(
                        platform=item["platform"],
                        external_id=item["external_id"],
                        title=item["title"],
                        sold_price=item["sold_price"],
                        condition=item.get("condition"),
                        category=item.get("category"),
                        brand=item.get("brand"),
                        sold_at=item.get("sold_at"),
                    ).on_conflict_do_nothing(constraint="uq_sold_platform_external")

                    await session.execute(stmt)
                    total += 1

            logger.info(f"[ebay_sold] Imported {len(sold)} sold items for '{keyword}'")

    finally:
        await scraper.close()

    return total
