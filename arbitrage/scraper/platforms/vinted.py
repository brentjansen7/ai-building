"""
Vinted scraper — mobile OAuth2 API.
Endpoint: https://www.vinted.nl/api/v2/catalog/items

Authentication: OAuth2 refresh token per account.
Rotate across multiple accounts to stay under rate limits.
"""

import logging
import os
import random
import string
from typing import List, Optional
from datetime import datetime

from scraper.base import BaseScraper

logger = logging.getLogger(__name__)

VINTED_API_BASE = "https://www.vinted.nl/api/v2"

# Load account tokens from env: VINTED_TOKENS=token1,token2,token3
_tokens = [t.strip() for t in os.getenv("VINTED_TOKENS", "").split(",") if t.strip()]
_token_index = 0

# Categories to scan — Vinted category IDs (NL)
VINTED_CATEGORIES = [
    {"id": "2050", "name": "elektronica"},
    {"id": "2064", "name": "cameras"},
    {"id": "1193", "name": "sport"},
    {"id": "2076", "name": "games"},
    {"id": "4",    "name": "kleding_heren"},
    {"id": "5",    "name": "kleding_dames"},
    {"id": "1231", "name": "schoenen"},
    {"id": "2218", "name": "horloges_sieraden"},
    {"id": "2",    "name": "kinderkleding"},
]


def _get_next_token() -> Optional[str]:
    """Round-robin token rotation across accounts."""
    global _token_index
    if not _tokens:
        return None
    token = _tokens[_token_index % len(_tokens)]
    _token_index += 1
    return token


def _random_device_id() -> str:
    """Generate a random Android device ID per session."""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=16))


class VintedScraper(BaseScraper):

    @property
    def platform(self) -> str:
        return "vinted"

    @property
    def requests_per_minute(self) -> int:
        # 30 req/min per token, multiply by account count
        base = 30
        return base * max(1, len(_tokens))

    async def fetch_listings(self) -> List[dict]:
        """Fetch new listings across all target categories."""
        all_listings = []

        for category in VINTED_CATEGORIES:
            try:
                listings = await self._fetch_category(category["id"], category["name"])
                all_listings.extend(listings)
                logger.info(f"[vinted] {category['name']}: {len(listings)} listings")
            except Exception as e:
                logger.error(f"[vinted] Failed {category['name']}: {e}")
                continue

        return all_listings

    async def _fetch_category(self, category_id: str, category_name: str) -> List[dict]:
        """Fetch listings for one category (2 pages)."""
        listings = []

        for page in range(1, 3):
            token = _get_next_token()
            headers = {
                "Accept": "application/json",
                "Accept-Language": "nl-NL,nl;q=0.9",
                "X-Anid": _random_device_id(),
                "User-Agent": "com.vinted.vinted/23.0.0 (Android 13; sdk=33)",
            }

            if token:
                headers["Authorization"] = f"Bearer {token}"

            params = {
                "catalog_ids": category_id,
                "order": "newest_first",
                "page": page,
                "per_page": 48,
            }

            try:
                response = await self.get(
                    f"{VINTED_API_BASE}/catalog/items",
                    params=params,
                    headers=headers,
                )
                data = response.json()

                for item in data.get("items", []):
                    listing = self._parse_item(item, category_name)
                    if listing:
                        listings.append(listing)

            except Exception as e:
                logger.warning(f"[vinted] Page {page} of {category_name} failed: {e}")
                break

        return listings

    def _parse_item(self, item: dict, category_name: str) -> dict | None:
        """Parse a Vinted API item into normalized format."""
        try:
            price_str = item.get("price", "0")
            price = float(str(price_str).replace(",", ".")) if price_str else 0.0

            if price <= 0:
                return None

            # Images
            photos = item.get("photos", [])
            image_urls = [
                p.get("url") or p.get("full_size_url", "")
                for p in photos if p.get("url") or p.get("full_size_url")
            ]

            # Posted date
            created_at = item.get("created_at_ts")
            posted_at = datetime.utcfromtimestamp(created_at) if created_at else None

            return {
                "platform": self.platform,
                "external_id": str(item.get("id", "")),
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "price": price,
                "condition": self.normalize_condition(item.get("status", "")),
                "category": category_name,
                "brand": item.get("brand_title"),
                "seller_id": str(item.get("user_id", "")),
                "location": item.get("city", ""),
                "url": item.get("url") or f"https://www.vinted.nl/items/{item.get('id')}",
                "image_urls": image_urls[:5],
                "posted_at": posted_at,
                "metadata": {
                    "size": item.get("size_title"),
                    "brand": item.get("brand_title"),
                    "color": item.get("color1"),
                    "is_shippable": item.get("can_be_sold"),
                    "favourite_count": item.get("favourite_count", 0),
                },
            }
        except Exception as e:
            logger.debug(f"[vinted] Parse error: {e}")
            return None
