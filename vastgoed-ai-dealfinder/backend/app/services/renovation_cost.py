from typing import Dict, List, Optional, Tuple
import structlog

logger = structlog.get_logger()


# ─────────────────────────────────────────────────────────────────────────────
# Nederlandse contractor prijzen 2024-2025 (inclusief arbeid + materialen)
# Gebaseerd op marktonderzoek (Verbouwkosten.nl, Werkspot, offerte-aanvragen)
# ─────────────────────────────────────────────────────────────────────────────

RENOVATION_COSTS: Dict[str, Dict] = {
    "schilderwerk": {
        "beschrijving": "Volledig schilderwerk binnen (muren + kozijnen + plafonds)",
        "min": 2500,
        "mid": 3500,
        "max": 6000,
        "per_sqm": True,
        "price_per_sqm": 18,     # ~€18/m² totale woonoppervlakte
        "min_base": 1500,
    },
    "keuken": {
        "beschrijving": "Complete nieuwe keuken inclusief montage, niet-inclusief apparatuur",
        "min": 5500,
        "mid": 9000,
        "max": 16000,
        "per_sqm": False,
    },
    "keuken_met_apparatuur": {
        "beschrijving": "Complete nieuwe keuken inclusief montage en apparatuur",
        "min": 8000,
        "mid": 13000,
        "max": 22000,
        "per_sqm": False,
    },
    "badkamer": {
        "beschrijving": "Complete nieuwe badkamer (douche, bad, toilet, tegels)",
        "min": 4500,
        "mid": 7000,
        "max": 12000,
        "per_sqm": False,
    },
    "toilet": {
        "beschrijving": "Nieuwe toiletgroep inclusief tegels en installatie",
        "min": 1200,
        "mid": 2000,
        "max": 3500,
        "per_sqm": False,
    },
    "vloeren": {
        "beschrijving": "Nieuwe vloerbedekking (laminaat/PVC), exclusief ondervloer",
        "min": 2500,
        "mid": 4000,
        "max": 7500,
        "per_sqm": True,
        "price_per_sqm": 45,     # ~€45/m² totale woonoppervlakte
        "min_base": 1500,
    },
    "vloeren_hout": {
        "beschrijving": "Parket of massief houten vloer",
        "min": 4000,
        "mid": 6500,
        "max": 11000,
        "per_sqm": True,
        "price_per_sqm": 75,
        "min_base": 2500,
    },
    "dak": {
        "beschrijving": "Dakrenovatie (pannen vervangen + dakisolatie)",
        "min": 5000,
        "mid": 9000,
        "max": 18000,
        "per_sqm": False,
    },
    "dak_plat": {
        "beschrijving": "Plat dak renovatie (bitumen/EPDM)",
        "min": 3500,
        "mid": 6000,
        "max": 10000,
        "per_sqm": False,
    },
    "isolatie_spouwmuur": {
        "beschrijving": "Spouwmuurisolatie inblazen",
        "min": 1200,
        "mid": 1800,
        "max": 3000,
        "per_sqm": False,
    },
    "isolatie_dak": {
        "beschrijving": "Dakisolatie (schuinend dak van binnen)",
        "min": 2500,
        "mid": 4000,
        "max": 7000,
        "per_sqm": False,
    },
    "isolatie_vloer": {
        "beschrijving": "Vloerisolatie kruipruimte",
        "min": 1500,
        "mid": 2500,
        "max": 4500,
        "per_sqm": False,
    },
    "ramen": {
        "beschrijving": "HR++ of triple glas (5 ramen inclusief montage)",
        "min": 3000,
        "mid": 5000,
        "max": 9000,
        "per_sqm": False,
    },
    "elektra": {
        "beschrijving": "Volledige elektra herinstallatie (meterkast + groepen)",
        "min": 3500,
        "mid": 5500,
        "max": 9500,
        "per_sqm": False,
    },
    "cv_systeem": {
        "beschrijving": "Nieuwe CV-ketel inclusief installatie",
        "min": 2000,
        "mid": 3500,
        "max": 5500,
        "per_sqm": False,
    },
    "leidingwerk": {
        "beschrijving": "Waterleidingen en afvoeren vervangen",
        "min": 2500,
        "mid": 4000,
        "max": 7000,
        "per_sqm": False,
    },
    "stucwerk": {
        "beschrijving": "Wanden en plafonds stuken/afwerken",
        "min": 2000,
        "mid": 3500,
        "max": 6000,
        "per_sqm": True,
        "price_per_sqm": 22,
        "min_base": 1500,
    },
    "kozijnen_deuren": {
        "beschrijving": "Vervanging binnenkozijnen en binnendeuren",
        "min": 2500,
        "mid": 4000,
        "max": 7000,
        "per_sqm": False,
    },
    "ventilatie": {
        "beschrijving": "Mechanisch ventilatiesysteem (WTW)",
        "min": 2000,
        "mid": 3500,
        "max": 6000,
        "per_sqm": False,
    },
}

# Stadskorrigatiefactoren (Amsterdam is 20% duurder, platteland 10% goedkoper)
CITY_FACTOR: Dict[str, float] = {
    "Amsterdam": 1.20,
    "Utrecht": 1.10,
    "Den Haag": 1.10,
    "'s-Gravenhage": 1.10,
    "Rotterdam": 1.05,
    "Eindhoven": 1.00,
    "Groningen": 0.95,
    "Tilburg": 0.95,
    "Breda": 0.95,
    "Nijmegen": 0.95,
    "Almere": 1.00,
    "Haarlem": 1.15,
    "Leiden": 1.10,
    "Maastricht": 0.95,
    "Zwolle": 0.90,
}


class RenovationCostEstimator:
    """
    Schat renovatiekosten zoals een aannemer dat zou doen.
    Gebaseerd op echte Nederlandse marktprijzen 2024-2025.
    """

    def estimate(
        self,
        items_to_renovate: List[str],
        size_sqm: int = 80,
        city: str = "Rotterdam",
        year_built: Optional[int] = None,
        klus_probability: float = 0.5,
    ) -> Dict:
        """
        Schat renovatiekosten voor een lijst van onderdelen.

        Returns:
            {
                cost_min: int,
                cost_mid: int,
                cost_max: int,
                breakdown_mid: {item: kosten},
                city_factor: float,
                notes: str,
            }
        """
        city_factor = CITY_FACTOR.get(city, 1.0)

        total_min = 0
        total_mid = 0
        total_max = 0
        breakdown = {}

        for item in items_to_renovate:
            cost = self._cost_for_item(item, size_sqm)
            if cost:
                total_min += int(cost["min"] * city_factor)
                total_mid += int(cost["mid"] * city_factor)
                total_max += int(cost["max"] * city_factor)
                breakdown[item] = int(cost["mid"] * city_factor)

        # Als er geen specifieke items zijn maar er wel klus-kans is
        if not breakdown and klus_probability > 0.5:
            # Aanname: gemiddelde kluswoning renovatie
            total_min = int(15000 * city_factor)
            total_mid = int(30000 * city_factor)
            total_max = int(55000 * city_factor)
            breakdown = {"algemene renovatie": total_mid}

        return {
            "cost_min": total_min,
            "cost_mid": total_mid,
            "cost_max": total_max,
            "breakdown_mid": breakdown,
            "city_factor": city_factor,
            "items_count": len(items_to_renovate),
            "notes": f"Prijzen inclusief arbeid en materialen, {city} factor {city_factor:.2f}x",
        }

    def _cost_for_item(self, item: str, size_sqm: int) -> Optional[Dict]:
        """Haal kosten op voor één renovatie-onderdeel."""
        # Directe match
        if item in RENOVATION_COSTS:
            cost_data = RENOVATION_COSTS[item]
        else:
            # Fuzzy match
            for key in RENOVATION_COSTS:
                if item.lower() in key.lower() or key.lower() in item.lower():
                    cost_data = RENOVATION_COSTS[key]
                    break
            else:
                logger.warning("Geen kosten data voor item", item=item)
                return None

        # Per m² berekening
        if cost_data.get("per_sqm") and size_sqm:
            calculated = max(
                cost_data["min_base"],
                size_sqm * cost_data["price_per_sqm"]
            )
            spread = calculated * 0.3
            return {
                "min": int(max(cost_data["min"], calculated - spread)),
                "mid": int(calculated),
                "max": int(min(cost_data["max"], calculated + spread * 1.5)),
            }
        else:
            return {
                "min": cost_data["min"],
                "mid": cost_data["mid"],
                "max": cost_data["max"],
            }

    def estimate_from_probability(
        self,
        klus_probability: float,
        size_sqm: int,
        year_built: Optional[int],
        city: str = "Rotterdam",
    ) -> Dict:
        """
        Schat kosten op basis van klus-waarschijnlijkheid en leeftijd.
        Handig als we geen specifieke items hebben.
        """
        year = year_built or 1975
        age = 2025 - year

        items = []

        # Bepaal items op basis van waarschijnlijkheid en leeftijd
        if klus_probability > 0.8 or age > 55:
            items = [
                "keuken", "badkamer", "toilet", "vloeren",
                "schilderwerk", "elektra", "cv_systeem",
                "isolatie_spouwmuur", "isolatie_dak", "ramen"
            ]
        elif klus_probability > 0.6 or age > 40:
            items = [
                "keuken", "badkamer", "vloeren",
                "schilderwerk", "cv_systeem"
            ]
        elif klus_probability > 0.3 or age > 25:
            items = ["schilderwerk", "vloeren", "badkamer"]
        else:
            items = ["schilderwerk"]

        return self.estimate(items, size_sqm, city, year_built, klus_probability)

    def get_full_renovation_estimate(
        self,
        size_sqm: int,
        city: str = "Rotterdam",
    ) -> Dict:
        """Schat kosten voor een VOLLEDIGE renovatie (worst case scenario)."""
        all_items = [
            "keuken", "badkamer", "toilet", "vloeren", "schilderwerk",
            "elektra", "cv_systeem", "leidingwerk", "isolatie_spouwmuur",
            "isolatie_dak", "ramen", "stucwerk", "dak"
        ]
        return self.estimate(all_items, size_sqm, city)
