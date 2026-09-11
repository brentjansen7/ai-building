"""
Marktplaats scraper — reverse-engineered internal JSON API.
Endpoint: https://www.marktplaats.nl/lrp/api/search
"""

import logging
from typing import List
from datetime import datetime, timezone

from scraper.base import BaseScraper

logger = logging.getLogger(__name__)

SEARCH_ENDPOINT = "https://www.marktplaats.nl/lrp/api/search"

# Categories to scan — mapped to Marktplaats category IDs
CATEGORIES = [
    {"id": "322", "name": "audio_hifi"},          # Audio, TV en Foto
    {"id": "31",  "name": "computers"},            # Computers en Software
    {"id": "278", "name": "cameras"},              # Fotografie en Camera
    {"id": "11",  "name": "elektronica"},          # Witgoed en Apparatuur
    {"id": "346", "name": "consoles_games"},       # Games en Gaming
    {"id": "16",  "name": "kleding_dames"},        # Mode
    {"id": "628", "name": "horloges"},             # Sieraden en Horloges
    {"id": "640", "name": "verzamelobjecten"},     # Verzamelingen
    {"id": "504", "name": "meubels"},              # Huis en Inrichting
]


class MarktplaatsScraper(BaseScraper):

    @property
    def platform(self) -> str:
        return "marktplaats"

    @property
    def requests_per_minute(self) -> int:
        return 40  # conservative — Cloudflare kicks in around 60

    async def fetch_listings(self) -> List[dict]:
        """Fetch all new listings across target categories."""
        all_listings = []

        for category in CATEGORIES:
            try:
                listings = await self._fetch_category(category["id"], category["name"])
                all_listings.extend(listings)
                logger.info(f"[marktplaats] {category['name']}: {len(listings)} listings")
            except Exception as e:
                logger.error(f"[marktplaats] Failed to fetch {category['name']}: {e}")
                continue

        return all_listings

    async def _fetch_category(self, category_id: str, category_name: str) -> List[dict]:
        """Fetch listings for a specific category (2 pages = 60 listings)."""
        listings = []

        for page in range(1, 3):  # 2 pages, 30 listings each
            params = {
                "l1CategoryId": category_id,
                "sortBy": "SORT_DATE",
                "sortOrder": "DECREASING",
                "size": 30,
                "offset": (page - 1) * 30,
            }

            headers = {
                "x-mp-vi": "true",
                "Referer": "https://www.marktplaats.nl/",
                "x-requested-with": "XMLHttpRequest",
            }

            try:
                response = await self.get(
                    SEARCH_ENDPOINT,
                    params=params,
                    headers=headers,
                )
                data = response.json()

                for item in data.get("listings", []):
                    listing = self._parse_listing(item, category_name)
                    if listing:
                        listings.append(listing)

            except Exception as e:
                logger.warning(f"[marktplaats] Page {page} of {category_name} failed: {e}")
                break

        return listings

    def _parse_listing(self, item: dict, category_name: str) -> dict | None:
        """Parse a raw Marktplaats API listing into normalized format."""
        try:
            listing_id = item.get("itemId") or item.get("l1Category", {}).get("id")
            price_info = item.get("priceInfo", {})
            price_cents = price_info.get("priceCents", 0)

            if not price_cents or price_cents < 100:  # skip free or < €1
                return None

            # Extract image URLs
            images = item.get("pictures", [])
            image_urls = [img.get("mediumUrl", "") for img in images if img.get("mediumUrl")]

            # Posted date
            date_str = item.get("date")
            posted_at = None
            if date_str:
                try:
                    posted_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except Exception:
                    pass

            return {
                "platform": self.platform,
                "external_id": str(item.get("itemId", "")),
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "price": price_cents / 100.0,
                "condition": self.normalize_condition(item.get("attributes", {}).get("condition", "")),
                "category": category_name,
                "brand": None,
                "seller_id": str(item.get("sellerId", "")),
                "location": item.get("location", {}).get("cityName", ""),
                "url": f"https://www.marktplaats.nl{item.get('vipUrl', '')}",
                "image_urls": image_urls[:5],
                "posted_at": posted_at,
                "metadata": {
                    "seller_name": item.get("sellerInformation", {}).get("sellerName"),
                    "priority": item.get("priorityProduct"),
                },
            }
        except Exception as e:
            logger.debug(f"[marktplaats] Parse error: {e}")
            return None
