from typing import List, Optional, Dict
from bs4 import BeautifulSoup
import structlog
import re

from app.scrapers.base import BaseScraper

logger = structlog.get_logger()


class ParariusScraper(BaseScraper):
    """Scraper voor Pararius.nl."""

    BASE_URL = "https://www.pararius.nl"
    SOURCE = "pararius"

    async def get_listing_urls(self, search_term: str = "", max_pages: int = 5) -> List[str]:
        """Haal koop-URLs op van Pararius."""
        urls = []
        base_search = f"{self.BASE_URL}/koopwoningen/nederland"

        for page_num in range(1, max_pages + 1):
            if page_num == 1:
                page_url = base_search
            else:
                page_url = f"{base_search}/page-{page_num}"

            try:
                page = await self._fetch_page(page_url, wait_for=".listing-search-item")
                content = await page.content()
                await page.close()

                soup = BeautifulSoup(content, "lxml")
                items = soup.select("a.listing-search-item__link--title")

                if not items:
                    logger.info("Geen items meer op pagina", page=page_num)
                    break

                for item in items:
                    href = item.get("href")
                    if href and "/koopwoning/" in href:
                        full_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href
                        urls.append(full_url)

                logger.debug("Pagina gescraped", page=page_num, found=len(items))
                await self._random_delay(2.0, 4.0)

            except Exception as e:
                logger.error("Pagina fout", page=page_num, error=str(e))
                break

        return list(set(urls))  # Dedupliceer

    async def parse_listing(self, url: str) -> Optional[Dict]:
        """Parse één Pararius listing."""
        try:
            page = await self._fetch_page(url)
            content = await page.content()
            await page.close()

            soup = BeautifulSoup(content, "lxml")
            return self._extract_data(soup, url)

        except Exception as e:
            logger.error("Listing parse fout", url=url, error=str(e))
            return None

    def _extract_data(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Extraheer data uit Pararius listing HTML."""

        # Basis info
        title = self._text(soup.select_one("h1.listing-detail-summary__title"))
        if not title:
            return None

        # Prijs
        price_elem = soup.select_one(".listing-detail-summary__price")
        price = self._parse_price(self._text(price_elem))

        # Adres
        address_elem = soup.select_one(".listing-detail-summary__location")
        address_text = self._text(address_elem) or ""

        # Postcode en stad extraheren
        postcode, city = self._parse_address(address_text)

        # Kenmerken
        features = {}
        for dt in soup.select(".listing-features__description dt"):
            key = self._text(dt)
            dd = dt.find_next_sibling("dd")
            val = self._text(dd) if dd else ""
            if key and val:
                features[key.lower()] = val

        size_sqm = self._parse_sqm(features.get("woonoppervlakte") or features.get("oppervlakte"))
        rooms = self._safe_int(features.get("kamers") or features.get("aantal kamers"))
        bedrooms = self._safe_int(features.get("slaapkamers"))
        year_built = self._safe_int(features.get("bouwjaar"))
        energy_label = features.get("energielabel")
        property_type = features.get("soort woning") or features.get("type")

        # Beschrijving
        desc_elem = soup.select_one(".listing-detail-description__additional")
        description = self._text(desc_elem)

        # Afbeeldingen
        images = []
        for img in soup.select(".photo-slider__photo-wrapper img"):
            src = img.get("src") or img.get("data-src")
            if src and src.startswith("http"):
                images.append(src)

        # Source ID van URL
        source_id = self._extract_source_id(url)

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
            "image_urls": images[:15],  # Max 15 afbeeldingen
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

    def _parse_address(self, address_text: str):
        """Extraheer postcode en stad."""
        postcode_match = re.search(r"\b(\d{4}\s?[A-Z]{2})\b", address_text)
        postcode = postcode_match.group(1).replace(" ", "") if postcode_match else None

        # Stad is gewoonlijk het laatste deel na postcode
        parts = address_text.strip().split()
        city = " ".join(parts[-2:]) if parts else "Onbekend"

        return postcode, city

    def _extract_source_id(self, url: str) -> str:
        """Extraheer ID van URL."""
        match = re.search(r"/koopwoning/([^/]+)/?$", url)
        return f"pararius_{match.group(1)}" if match else f"pararius_{hash(url)}"
