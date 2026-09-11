"""
BVA Auctions scraper - Dutch bailiff/liquidation platform.
HTML-based scraper using BeautifulSoup + LD+JSON parsing.
"""

import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from bs4 import BeautifulSoup
import json
import re

logger = logging.getLogger(__name__)

BVA_URL_BASE = "https://www.bva-auctions.nl"


@dataclass
class BVALot:
    """BVA auction lot."""
    external_id: str
    title: str
    description: str
    current_bid: float
    estimate_low: Optional[float]
    estimate_high: Optional[float]
    lot_number: str
    url: str
    image_urls: List[str]
    auction_id: str
    category: str
    condition: Optional[str]
    raw_data: Dict[str, Any]


class BVAAuctionsScraper:
    """
    Scraper for BVA Auctions Dutch bailiff/liquidation platform.

    Rate limit: ~1 req/sec (light protection)
    Anti-bot: Basic Cloudflare, no heavy JS challenge
    """

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = httpx.Client(
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
                "Referer": "https://www.bva-auctions.nl/",
            },
        )

    def close(self):
        """Close HTTP session."""
        self.session.close()

    async def fetch_active_auctions(self) -> List[str]:
        """
        Fetch list of active auction IDs.

        Returns:
            List of auction IDs
        """
        try:
            logger.info("Fetching active BVA auctions")
            url = f"{BVA_URL_BASE}/nl/auction/list"

            response = self.session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Find auction links
            auction_ids = []
            auction_links = soup.select('a[href*="/nl/auction/"]')

            for link in auction_links:
                href = link.get("href", "")
                match = re.search(r"/auction/(\d+)", href)
                if match:
                    auction_ids.append(match.group(1))

            # Deduplicate
            auction_ids = list(set(auction_ids))
            logger.info(f"Found {len(auction_ids)} active auctions")
            return auction_ids

        except Exception as e:
            logger.error(f"Failed to fetch active auctions: {e}")
            return []

    async def fetch_auction_lots(
        self,
        auction_id: str,
        page: int = 1,
    ) -> List[BVALot]:
        """
        Fetch all lots from a specific auction.

        Args:
            auction_id: BVA auction ID
            page: Page number for pagination

        Returns:
            List of BVALot objects
        """
        try:
            url = f"{BVA_URL_BASE}/nl/lot/list"
            params = {"auctionId": auction_id, "page": page}

            logger.debug(f"Fetching BVA auction {auction_id} page {page}")
            response = self.session.get(url, params=params)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            lots = []

            # Find lot cards
            lot_cards = soup.select('[data-lot-id], .lot-item, [class*="lot"]')

            for card in lot_cards:
                try:
                    lot = self._parse_lot_card(card, auction_id)
                    if lot:
                        lots.append(lot)
                except Exception as e:
                    logger.warning(f"Failed to parse lot card: {e}")
                    continue

            logger.info(f"Fetched {len(lots)} lots from auction {auction_id}")
            return lots

        except Exception as e:
            logger.error(f"Failed to fetch auction {auction_id}: {e}")
            return []

    def _parse_lot_card(self, card, auction_id: str) -> Optional[BVALot]:
        """Parse lot card HTML into BVALot object."""

        # Extract lot ID
        lot_id = card.get("data-lot-id")
        if not lot_id:
            # Try to extract from link
            link = card.find("a")
            if link:
                href = link.get("href", "")
                match = re.search(r"/lot/(\d+)", href)
                if match:
                    lot_id = match.group(1)

        if not lot_id:
            return None

        # Extract title
        title_el = card.select_one(".lot-name, h3, [class*='title']")
        title = title_el.text.strip() if title_el else ""

        if not title:
            return None

        # Extract lot number
        lot_num_el = card.select_one(".lot-number, [class*='number']")
        lot_number = lot_num_el.text.strip() if lot_num_el else lot_id

        # Extract current bid
        bid_el = card.select_one(".lot-price, [class*='price']:first-child")
        bid_text = bid_el.text if bid_el else "€ 0"
        current_bid = self._parse_price(bid_text)

        # Extract estimate
        estimate_el = card.select_one("[class*='estimate']")
        estimate = estimate_el.text if estimate_el else ""
        estimate_low, estimate_high = self._parse_estimate(estimate)

        # Extract description
        desc_el = card.select_one("[class*='description']")
        description = desc_el.text.strip() if desc_el else ""

        # Extract images
        images = []
        img_els = card.select("img")
        for img in img_els:
            src = img.get("src", "")
            if src and "image" in src.lower():
                if src.startswith("http"):
                    images.append(src)
                else:
                    images.append(BVA_URL_BASE + src)

        # Extract category
        category_el = card.select_one("[class*='category']")
        category = category_el.text.strip() if category_el else "General"

        # Build URL
        url = f"{BVA_URL_BASE}/nl/lot/{lot_id}"

        # Check for LD+JSON data
        raw_data = {}
        script_tag = card.find_parent().find("script", {"type": "application/ld+json"})
        if script_tag:
            try:
                raw_data = json.loads(script_tag.string)
            except:
                pass

        return BVALot(
            external_id=lot_id,
            title=title,
            description=description,
            current_bid=current_bid,
            estimate_low=estimate_low,
            estimate_high=estimate_high,
            lot_number=lot_number,
            url=url,
            image_urls=images,
            auction_id=auction_id,
            category=category,
            condition=None,
            raw_data=raw_data,
        )

    @staticmethod
    def _parse_price(price_text: str) -> float:
        """Parse price from text (e.g., '€ 150,00' -> 150.0)."""
        # Remove currency symbols and spaces
        cleaned = re.sub(r"[€$£\s]", "", price_text)
        # Replace comma with dot for decimals
        cleaned = cleaned.replace(",", ".")
        try:
            return float(cleaned) if cleaned else 0.0
        except:
            return 0.0

    @staticmethod
    def _parse_estimate(estimate_text: str) -> tuple:
        """Parse estimate range (e.g., '€100 - €200' -> (100, 200))."""
        if not estimate_text:
            return None, None

        # Try to find two numbers
        numbers = re.findall(r"€?\s*([\d.,]+)", estimate_text)
        if len(numbers) >= 2:
            try:
                low = BVAAuctionsScraper._parse_price(numbers[0])
                high = BVAAuctionsScraper._parse_price(numbers[1])
                return low, high
            except:
                pass

        return None, None


async def scrape_bva_auctions() -> List[Dict[str, Any]]:
    """
    Convenience function: scrape all active BVA lots and return as dicts for DB.
    """
    scraper = BVAAuctionsScraper()
    try:
        # Get active auction IDs
        auction_ids = await scraper.fetch_active_auctions()

        if not auction_ids:
            logger.warning("No active BVA auctions found")
            return []

        # Scrape first 5 auctions (limit for testing)
        all_lots = []
        for auction_id in auction_ids[:5]:
            lots = await scraper.fetch_auction_lots(auction_id)
            all_lots.extend(lots)

        # Convert to database-friendly format
        result = []
        for lot in all_lots:
            result.append({
                "platform": "bva_auctions",
                "external_id": lot.external_id,
                "title": lot.title,
                "description": lot.description,
                "price": lot.current_bid,
                "condition": lot.condition,
                "category": lot.category,
                "url": lot.url,
                "image_urls": lot.image_urls,
                "posted_at": datetime.now(),
                "seller_id": f"bva_{lot.auction_id}",
                "location": "NL",
                "metadata": {
                    "lot_number": lot.lot_number,
                    "auction_id": lot.auction_id,
                    "estimate_low": lot.estimate_low,
                    "estimate_high": lot.estimate_high,
                }
            })

        return result

    finally:
        scraper.close()
