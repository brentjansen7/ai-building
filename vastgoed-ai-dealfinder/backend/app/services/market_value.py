from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, text
from datetime import datetime, timedelta
import structlog
import math

from app.models.db import Comp

logger = structlog.get_logger()


# ─────────────────────────────────────────────────────────────────────────────
# Stad-gemiddelde prijzen per m² (2024-2025 data)
# Bron: NVM, CBS, Funda marktrapportages
# ─────────────────────────────────────────────────────────────────────────────

CITY_PRICE_PER_SQM: Dict[str, Dict] = {
    "Amsterdam": {"price_sqm": 8200, "trend_pct": 3.5, "region": "Randstad"},
    "Utrecht": {"price_sqm": 6500, "trend_pct": 4.0, "region": "Randstad"},
    "Den Haag": {"price_sqm": 5800, "trend_pct": 3.0, "region": "Randstad"},
    "'s-Gravenhage": {"price_sqm": 5800, "trend_pct": 3.0, "region": "Randstad"},
    "Haarlem": {"price_sqm": 7200, "trend_pct": 3.5, "region": "Randstad"},
    "Leiden": {"price_sqm": 6200, "trend_pct": 3.5, "region": "Randstad"},
    "Rotterdam": {"price_sqm": 5200, "trend_pct": 5.0, "region": "Randstad"},
    "Eindhoven": {"price_sqm": 4800, "trend_pct": 4.5, "region": "Brabant"},
    "Breda": {"price_sqm": 4200, "trend_pct": 3.5, "region": "Brabant"},
    "Tilburg": {"price_sqm": 3800, "trend_pct": 4.0, "region": "Brabant"},
    "Nijmegen": {"price_sqm": 4500, "trend_pct": 3.5, "region": "Gelderland"},
    "Arnhem": {"price_sqm": 3600, "trend_pct": 3.0, "region": "Gelderland"},
    "Zwolle": {"price_sqm": 3800, "trend_pct": 4.0, "region": "Overijssel"},
    "Enschede": {"price_sqm": 2800, "trend_pct": 2.5, "region": "Overijssel"},
    "Groningen": {"price_sqm": 3200, "trend_pct": 5.5, "region": "Groningen"},
    "Almere": {"price_sqm": 4200, "trend_pct": 4.0, "region": "Flevoland"},
    "Amersfoort": {"price_sqm": 5200, "trend_pct": 3.5, "region": "Utrecht"},
    "Maastricht": {"price_sqm": 3500, "trend_pct": 2.5, "region": "Limburg"},
    "Venlo": {"price_sqm": 2800, "trend_pct": 2.0, "region": "Limburg"},
    "Dordrecht": {"price_sqm": 3400, "trend_pct": 4.0, "region": "Zuid-Holland"},
    "Delft": {"price_sqm": 5500, "trend_pct": 3.5, "region": "Zuid-Holland"},
    "Alkmaar": {"price_sqm": 4500, "trend_pct": 3.0, "region": "Noord-Holland"},
    "Zaandam": {"price_sqm": 4800, "trend_pct": 4.0, "region": "Noord-Holland"},
}

# Standaard als stad niet gevonden
DEFAULT_PRICE_PER_SQM = 4000


class MarketValuationEngine:
    """
    Schat marktwaarde op basis van:
    1. Vergelijkbare verkopen (comps) uit database
    2. Prijs per m² in stad/buurt
    3. WOZ waarde als referentie
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def estimate(
        self,
        price_ask: int,
        size_sqm: int,
        city: str,
        postcode: Optional[str],
        woz_value: Optional[int],
        year_built: Optional[int],
        rooms: Optional[int],
        klus_probability: float = 0.0,
        reno_cost_mid: int = 0,
    ) -> Dict:
        """
        Schat marktwaarde voor en na renovatie.

        Returns:
            {
                price_per_sqm_ask: int,
                neighborhood_price_per_sqm: int,
                estimated_current_value: int,
                estimated_value_after_reno: int,
                comparable_count: int,
                method: str,
                discount_pct: float,  # hoeveel % onder markt
            }
        """
        # 1. Bepaal buurtprijs per m²
        neighborhood_sqm = await self._get_neighborhood_price_sqm(postcode, city)

        # 2. Schat huidige marktwaarde (ZONDER renovatie)
        current_market_value = self._estimate_current_value(
            size_sqm, neighborhood_sqm, woz_value, year_built, klus_probability
        )

        # 3. Schat waarde NA renovatie
        value_after_reno = self._estimate_post_reno_value(
            size_sqm, neighborhood_sqm, year_built, klus_probability
        )

        # 4. Prijs per m² van vraagprijs
        price_per_sqm_ask = int(price_ask / size_sqm) if size_sqm else 0

        # 5. Comps ophalen voor verificatie
        comps = await self._get_comps(postcode, city, size_sqm)

        if comps:
            comps_avg = sum(c["price_per_sqm"] for c in comps) / len(comps)
            neighborhood_sqm = int((neighborhood_sqm * 0.4) + (comps_avg * 0.6))
            method = f"comps_weighted ({len(comps)} comp(s))"
        else:
            method = "city_average"

        discount_pct = round(
            ((current_market_value - price_ask) / current_market_value * 100),
            1
        ) if current_market_value > 0 else 0.0

        return {
            "price_per_sqm_ask": price_per_sqm_ask,
            "neighborhood_price_per_sqm": neighborhood_sqm,
            "estimated_current_value": current_market_value,
            "estimated_value_after_reno": value_after_reno,
            "comparable_count": len(comps),
            "method": method,
            "discount_pct": discount_pct,
        }

    async def _get_neighborhood_price_sqm(
        self, postcode: Optional[str], city: str
    ) -> int:
        """Haal prijs per m² op voor buurt/stad."""

        # 1. Probeer postcode-specifieke comps in DB
        if postcode and len(postcode) >= 6:
            postcode4 = postcode[:4]
            try:
                result = await self.db.execute(
                    text("""
                        SELECT AVG(sold_price::float / NULLIF(size_sqm, 0)) as avg_sqm_price
                        FROM comps
                        WHERE postcode4 = :pc4
                          AND sold_date > NOW() - INTERVAL '18 months'
                          AND size_sqm > 0
                          AND sold_price > 0
                    """),
                    {"pc4": postcode4}
                )
                row = result.fetchone()
                if row and row[0]:
                    return int(row[0])
            except Exception as e:
                logger.warning("Comps DB query fout", error=str(e))

        # 2. Fallback: stadsgemiddelde
        city_data = CITY_PRICE_PER_SQM.get(city)
        if city_data:
            return city_data["price_sqm"]

        # 3. Regio match (Amsterdam-Noord → Amsterdam)
        for key, data in CITY_PRICE_PER_SQM.items():
            if key.lower() in city.lower() or city.lower() in key.lower():
                return data["price_sqm"]

        return DEFAULT_PRICE_PER_SQM

    def _estimate_current_value(
        self,
        size_sqm: int,
        sqm_price: int,
        woz_value: Optional[int],
        year_built: Optional[int],
        klus_probability: float,
    ) -> int:
        """
        Schat huidige marktwaarde.
        Kluswoningen zijn typisch 15-30% goedkoper dan marktwaarde.
        """
        base_value = size_sqm * sqm_price if size_sqm else (woz_value or 200000)

        # Klus korting: hoe meer renovatie nodig, hoe lager de waarde
        klus_discount = min(0.30, klus_probability * 0.35)
        current_value = base_value * (1 - klus_discount)

        # WOZ als extra referentie
        if woz_value and woz_value > 0:
            # Gewogen gemiddelde: 60% comps, 40% WOZ
            current_value = (current_value * 0.60) + (woz_value * 0.40)

        return int(current_value)

    def _estimate_post_reno_value(
        self,
        size_sqm: int,
        sqm_price: int,
        year_built: Optional[int],
        klus_probability: float,
    ) -> int:
        """
        Schat waarde NA volledige renovatie.
        Na renovatie bereikt woning 85-95% van volledig nieuwbouwwaarde.
        """
        base_value = size_sqm * sqm_price if size_sqm else 200000

        # Na renovatie: oud pand met nieuwe inrichting = ~88% van markt
        # (Niet 100% want ligging, bouwjaar structuur blijft oud)
        reno_factor = 0.88

        if klus_probability > 0.8:
            reno_factor = 0.90  # Meer ruimte voor waardestijging
        elif klus_probability > 0.5:
            reno_factor = 0.88

        return int(base_value * reno_factor)

    async def _get_comps(
        self, postcode: Optional[str], city: str, size_sqm: int
    ) -> List[Dict]:
        """Haal vergelijkbare verkopen op uit database."""
        if not self.db:
            return []

        try:
            postcode4 = postcode[:4] if postcode and len(postcode) >= 4 else None

            # Min/max grootte: ±30%
            min_sqm = int(size_sqm * 0.7) if size_sqm else 40
            max_sqm = int(size_sqm * 1.3) if size_sqm else 200

            cutoff_date = datetime.now() - timedelta(days=548)  # ~18 maanden

            query = select(Comp).where(
                and_(
                    Comp.sold_date >= cutoff_date,
                    Comp.size_sqm >= min_sqm,
                    Comp.size_sqm <= max_sqm,
                    Comp.sold_price > 0,
                )
            )

            if postcode4:
                query = query.where(Comp.postcode4 == postcode4)
            else:
                query = query.where(Comp.city.ilike(f"%{city}%"))

            query = query.limit(20)
            result = await self.db.execute(query)
            comps = result.scalars().all()

            return [
                {
                    "price": c.sold_price,
                    "size_sqm": c.size_sqm,
                    "price_per_sqm": int(c.sold_price / c.size_sqm),
                    "sold_date": c.sold_date,
                }
                for c in comps
                if c.size_sqm and c.size_sqm > 0
            ]

        except Exception as e:
            logger.warning("Comps query fout", error=str(e))
            return []
