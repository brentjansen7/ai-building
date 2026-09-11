"""
Auctionet scraper - semi-public API, easiest platform to start with.
https://auctionet.com/api/v1/items
"""

import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

AUCTIONET_API_BASE = "https://auctionet.com/api/v1"

# Category mapping for Auctionet
CATEGORY_MAP = {
    "silver": "Antique Silver",
    "ceramics": "Ceramics & Glass",
    "art": "Art & Paintings",
    "furniture": "Furniture",
    "watches": "Watches",
    "jewelry": "Jewelry",
    "books": "Books",
    "vintage": "Vintage",
}


@dataclass
class AuctionetItem:
    """Auctionet auction item."""
    external_id: str
    title: str
    description: str
    current_bid: float
    estimated_value: Optional[float]
    category: str
    url: str
    image_urls: List[str]
    end_time: datetime
    auction_house: str
    condition: Optional[str]
    country: str
    raw_data: Dict[str, Any]


class AuctionetScraper:
    """
    Scraper for Auctionet semi-public API.

    Rate limit: ~1 request per second (respectful)
    Authentication: None required for public search
    """

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = httpx.Client(
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )

    def close(self):
        """Close HTTP session."""
        self.session.close()

    async def fetch_open_items(
        self,
        category: Optional[str] = None,
        country: str = "nl",
        page: int = 1,
        per_page: int = 100,
    ) -> List[AuctionetItem]:
        """
        Fetch open auction items from Auctionet.

        Args:
            category: Category filter (e.g., 'silver', 'ceramics')
            country: Country code (default: 'nl' for Netherlands)
            page: Page number for pagination
            per_page: Items per page (max 100)

        Returns:
            List of AuctionetItem objects
        """
        params = {
            "status": "open",
            "country": country,
            "page": page,
            "per_page": min(per_page, 100),
        }

        if category and category in CATEGORY_MAP:
            params["category"] = category

        try:
            logger.info(f"Fetching Auctionet items: {params}")
            response = self.session.get(f"{AUCTIONET_API_BASE}/items", params=params)
            response.raise_for_status()

            data = response.json()
            items = []

            # Parse API response
            for item_data in data.get("items", []):
                try:
                    item = self._parse_item(item_data)
                    items.append(item)
                except Exception as e:
                    logger.warning(f"Failed to parse item: {item_data.get('id')} - {e}")
                    continue

            logger.info(f"Fetched {len(items)} items from Auctionet")
            return items

        except httpx.RequestError as e:
            logger.error(f"Request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []

    def _parse_item(self, item_data: Dict[str, Any]) -> AuctionetItem:
        """Parse raw API item data into AuctionetItem."""

        # Extract images
        images = []
        if "images" in item_data:
            if isinstance(item_data["images"], list):
                images = item_data["images"]
            elif isinstance(item_data["images"], dict):
                images = item_data["images"].get("urls", [])

        # Parse end time
        end_time = None
        if item_data.get("end_date"):
            try:
                end_time = datetime.fromisoformat(
                    item_data["end_date"].replace("Z", "+00:00")
                )
            except:
                pass

        # Current bid (may be estimate if no bids)
        current_bid = float(item_data.get("current_bid") or item_data.get("estimate") or 0)
        estimated = float(item_data.get("estimate") or 0)

        return AuctionetItem(
            external_id=str(item_data.get("id")),
            title=item_data.get("title", ""),
            description=item_data.get("description", ""),
            current_bid=current_bid,
            estimated_value=estimated if estimated > 0 else None,
            category=item_data.get("category", ""),
            url=f"https://auctionet.com/item/{item_data.get('id')}",
            image_urls=images,
            end_time=end_time,
            auction_house=item_data.get("auction_house", ""),
            condition=item_data.get("condition"),
            country=item_data.get("country", ""),
            raw_data=item_data,
        )

    async def fetch_sold_items(
        self,
        category: Optional[str] = None,
        country: str = "nl",
        days: int = 30,
    ) -> List[AuctionetItem]:
        """
        Fetch recently sold items for price history.

        Args:
            category: Category filter
            country: Country code
            days: How many days back to fetch

        Returns:
            List of sold AuctionetItem objects
        """
        params = {
            "status": "sold",
            "country": country,
            "days": days,
            "per_page": 100,
        }

        if category and category in CATEGORY_MAP:
            params["category"] = category

        all_items = []
        page = 1

        try:
            while True:
                params["page"] = page
                response = self.session.get(f"{AUCTIONET_API_BASE}/items", params=params)
                response.raise_for_status()

                data = response.json()
                items = data.get("items", [])

                if not items:
                    break

                for item_data in items:
                    try:
                        item = self._parse_item(item_data)
                        all_items.append(item)
                    except Exception as e:
                        logger.warning(f"Failed to parse sold item: {e}")
                        continue

                # Check if there are more pages
                if len(items) < params["per_page"]:
                    break

                page += 1

            logger.info(f"Fetched {len(all_items)} sold items from Auctionet")
            return all_items

        except Exception as e:
            logger.error(f"Error fetching sold items: {e}")
            return all_items


async def scrape_auctionet_open(
    category: Optional[str] = None,
    country: str = "nl",
) -> List[Dict[str, Any]]:
    """
    Convenience function: scrape open Auctionet items and return as dicts for DB.
    """
    scraper = AuctionetScraper()
    try:
        items = await scraper.fetch_open_items(category=category, country=country)

        # Convert to database-friendly format
        result = []
        for item in items:
            result.append({
                "platform": "auctionet",
                "external_id": item.external_id,
                "title": item.title,
                "description": item.description,
                "price": item.current_bid,
                "condition": item.condition,
                "category": item.category,
                "url": item.url,
                "image_urls": item.image_urls,
                "posted_at": item.end_time,
                "seller_id": item.auction_house,
                "location": item.country,
                "metadata": {
                    "estimated_value": item.estimated_value,
                    "auction_house": item.auction_house,
                    "end_time": item.end_time.isoformat() if item.end_time else None,
                }
            })

        return result
    finally:
        scraper.close()
