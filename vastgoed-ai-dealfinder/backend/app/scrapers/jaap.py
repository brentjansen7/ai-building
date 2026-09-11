from typing import List, Optional, Dict
from bs4 import BeautifulSoup
import structlog
import re

from app.scrapers.base import BaseScraper

logger = structlog.get_logger()


class JaapScraper(BaseScraper):
    """Scraper voor Jaap.nl."""

    BASE_URL = "https://www.jaap.nl"
    SOURCE = "jaap"

    async def get_listing_urls(self, search_term: str = "", max_pages: int = 5) -> List[str]:
        """Haal listing URLs op van Jaap.nl."""
        urls = []

        for page_num in range(1, max_pages + 1):
            if page_num == 1:
                page_url = f"{self.BASE_URL}/koophuizen/heel-nederland/"
            else:
                page_url = f"{self.BASE_URL}/koophuizen/heel-nederland/p{page_num}/"

            try:
                page = await self._fetch_page(page_url, wait_for=".property-list")
                content = await page.content()
                await page.close()

                soup = BeautifulSoup(content, "lxml")
                links = soup.select("a.property-list-item-title")

                if not links:
                    break

                for link in links:
                    href = link.get("href")
                    if href:
                        full_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href
                        urls.append(full_url)

                await self._random_delay(2.0, 4.5)

            except Exception as e:
                logger.error("Jaap pagina fout", page=page_num, error=str(e))
                break

        return list(set(urls))

    async def parse_listing(self, url: str) -> Optional[Dict]:
        """Parse één Jaap listing."""
        try:
            page = await self._fetch_page(url)
            content = await page.content()
            await page.close()

            soup = BeautifulSoup(content, "lxml")
            return self._extract_data(soup, url)

        except Exception as e:
            logger.error("Jaap listing fout", url=url, error=str(e))
            return None

    def _extract_data(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Extraheer data uit Jaap.nl listing HTML."""

        title = self._text(soup.select_one("h1.property-header-title"))
        if not title:
            return None

        # Prijs
        price_elem = soup.select_one(".property-price")
        price = self._parse_price(self._text(price_elem))

        # Adres
        address_elem = soup.select_one(".property-header-address")
        address_text = self._text(address_elem) or ""

        postcode_match = re.search(r"\b(\d{4}\s?[A-Z]{2})\b", address_text)
        postcode = postcode_match.group(1).replace(" ", "") if postcode_match else None
        city_match = re.search(r"\d{4}\s?[A-Z]{2}\s+(.+)$", address_text)
        city = city_match.group(1).strip() if city_match else "Onbekend"

        # Kenmerken
        features = {}
        for row in soup.select(".property-features-item"):
            label = self._text(row.select_one(".property-features-label"))
            value = self._text(row.select_one(".property-features-value"))
            if label and value:
                features[label.lower()] = value

        size_sqm = self._parse_sqm(features.get("woonoppervlak") or features.get("oppervlakte"))
        rooms = self._safe_int(features.get("kamers"))
        bedrooms = self._safe_int(features.get("slaapkamers"))
        year_built = self._safe_int(features.get("bouwjaar"))
        energy_label = features.get("energielabel")
        property_type = features.get("woningtype")

        # Beschrijving
        desc_elem = soup.select_one(".property-description")
        description = self._text(desc_elem)

        # Afbeeldingen
        images = []
        for img in soup.select(".property-images img"):
            src = img.get("src") or img.get("data-src")
            if src and src.startswith("http"):
                images.append(src)

        source_id = f"jaap_{self._extract_source_id(url)}"

        return {
            "source": self.SOURCE,
            "source_id": source_id,
            "url": url,
            "title": title,
            "price_ask": price,
            "address": address_text,
            "city": city,
            "postcode": postcode,
            "size_sqm": size_sqm,
            "rooms": rooms,
            "bedrooms": bedrooms,
            "year_built": year_built,
            "property_type": property_type,
            "energy_label": energy_label,
            "description": description,
            "image_urls": images[:15],
            "images_count": len(images),
        }

    def _text(self, elem) -> Optional[str]:
        if elem is None:
            return None
        return elem.get_text(separator=" ", strip=True)

    def _safe_int(self, val: Optional[str]) -> Optional[int]:
        if not val:
            return None
        digits = re.sub(r"[^\d]", "", val)
        return int(digits) if digits else None

    def _extract_source_id(self, url: str) -> str:
        match = re.search(r"/(\d+)/?$", url)
        return match.group(1) if match else str(hash(url))
