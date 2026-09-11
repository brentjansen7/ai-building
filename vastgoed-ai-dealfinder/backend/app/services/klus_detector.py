from typing import Dict, List, Optional, Tuple
import anthropic
import structlog
import re

logger = structlog.get_logger()


# Klus-gerelateerde trefwoorden gerankt op sterkte
KLUS_KEYWORDS: Dict[str, float] = {
    # Sterk (0.8-1.0)
    "kluswoning": 1.0,
    "klus woning": 1.0,
    "opknapper": 0.95,
    "renovatie nodig": 0.95,
    "projectwoning": 0.9,
    "project woning": 0.9,
    "handige klusser": 0.9,
    "fixer-upper": 0.9,
    "geheel te renoveren": 0.9,
    "volledig te renoveren": 0.9,
    "grondige renovatie": 0.85,
    "renovatiewoning": 0.85,
    "te renoveren": 0.8,
    "renovatieproject": 0.8,
    "verbouwingswoning": 0.8,
    # Matig (0.4-0.79)
    "onderhoud nodig": 0.7,
    "verouderd": 0.6,
    "verouderde": 0.6,
    "origineel": 0.55,
    "jaren": 0.4,
    "karakteristiek": 0.35,
    "monumentaal": 0.3,
    "authentiek": 0.3,
    # Gedeeltelijke renovatie
    "nieuwe keuken": 0.5,
    "nieuwe badkamer": 0.5,
    "nieuwe vloer": 0.4,
    "gestuct": 0.35,
    "schilderwerk": 0.3,
    # Oud/beschadigd indicatoren
    "oud": 0.3,
    "achterstallig": 0.75,
    "ingrijpende verbouwing": 0.85,
    "aan te pakken": 0.6,
    "werkende staat": 0.65,
    "bouwvallig": 0.9,
}


class KlusDetector:
    """
    Detecteer of een woning waarschijnlijk een kluswoning is via:
    1. Keyword analyse van de beschrijving
    2. Claude Vision analyse van foto's
    """

    def __init__(self, anthropic_api_key: str):
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)

    async def analyze(
        self,
        description: Optional[str],
        title: Optional[str],
        image_urls: Optional[List[str]] = None,
        year_built: Optional[int] = None,
    ) -> Dict:
        """
        Volledig klus-analyse van een listing.

        Returns:
            {
                klus_probability: 0.0-1.0,
                klus_keywords: [...],
                text_score: 0.0-1.0,
                image_score: 0.0-1.0,
                description: "Beschrijving van bevindingen",
                items_to_renovate: [...],
            }
        """
        # 1. Text analyse
        text_result = self._analyze_text(description or "", title or "")

        # 2. Leeftijdsscore
        age_score = self._age_score(year_built)

        # 3. Afbeeldingen analyse (indien aanwezig)
        image_score = 0.0
        image_details = []
        if image_urls:
            try:
                image_score, image_details = await self._analyze_images(image_urls[:5])
            except Exception as e:
                logger.warning("Image analyse mislukt", error=str(e))

        # 4. Gecombineerde score
        if image_urls and image_score > 0:
            # Als we afbeeldingen hebben: 40% tekst, 45% beelden, 15% leeftijd
            combined = (text_result["score"] * 0.40) + (image_score * 0.45) + (age_score * 0.15)
        else:
            # Zonder beelden: 75% tekst, 25% leeftijd
            combined = (text_result["score"] * 0.75) + (age_score * 0.25)

        # Items die gerenoveerd moeten worden
        items = self._estimate_renovation_items(
            combined, year_built, text_result["keywords"], image_details
        )

        description_text = self._build_description(combined, text_result, image_score, year_built)

        return {
            "klus_probability": round(min(1.0, combined), 3),
            "klus_keywords": text_result["keywords"],
            "text_score": round(text_result["score"], 3),
            "image_score": round(image_score, 3),
            "age_score": round(age_score, 3),
            "description": description_text,
            "items_to_renovate": items,
        }

    def _analyze_text(self, description: str, title: str) -> Dict:
        """Analyseer beschrijvingstekst op klus-indicatoren."""
        combined_text = (title + " " + description).lower()
        found_keywords = []
        max_score = 0.0

        for keyword, weight in KLUS_KEYWORDS.items():
            if keyword in combined_text:
                found_keywords.append(keyword)
                max_score = max(max_score, weight)

        # Bonus: meerdere klus-woorden verhogen score
        if len(found_keywords) >= 3:
            max_score = min(1.0, max_score + 0.10)
        elif len(found_keywords) >= 2:
            max_score = min(1.0, max_score + 0.05)

        return {"score": max_score, "keywords": found_keywords}

    def _age_score(self, year_built: Optional[int]) -> float:
        """Oudere woningen hebben meer kans op renovatie nodig."""
        if not year_built:
            return 0.2  # Onbekend: kleine kans
        age = 2025 - year_built
        if age > 60:
            return 0.6
        elif age > 40:
            return 0.4
        elif age > 25:
            return 0.2
        else:
            return 0.05

    async def _analyze_images(self, image_urls: List[str]) -> Tuple[float, List[str]]:
        """
        Analyseer foto's met Claude Vision om de staat te beoordelen.
        Geeft score 0-1 terug (1 = slecht / renovatie nodig).
        """
        scores = []
        details = []

        prompt = """Beoordeel de staat van deze kamer/ruimte.

Geef een getal tussen 0.0 en 1.0:
- 0.0 = modern en goed onderhouden
- 0.3 = redelijk staat maar niet recent gerenoveerd
- 0.6 = zichtbaar verouderd, meerdere elementen aan vervanging toe
- 0.8 = slechte staat, aanzienlijke renovatie nodig
- 1.0 = bouwvallig, complete renovatie vereist

Kijk naar: vloer, muren, plafond, keuken/badkamer inrichting, schilderwerk, kozijnen.

Antwoord ALLEEN met: [cijfer] [1-2 woorden uitleg]
Voorbeeld: 0.7 verouderde keuken"""

        for url in image_urls:
            try:
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=50,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {"type": "url", "url": url},
                                },
                                {"type": "text", "text": prompt},
                            ],
                        }
                    ],
                )

                text = response.content[0].text.strip()
                score_match = re.search(r"(\d+\.?\d*)", text)
                if score_match:
                    score = float(score_match.group(1))
                    scores.append(min(1.0, score))
                    details.append(text)

            except Exception as e:
                logger.warning("Image analyse fout", url=url[:50], error=str(e))
                continue

        if not scores:
            return 0.0, []

        avg_score = sum(scores) / len(scores)
        return avg_score, details

    def _estimate_renovation_items(
        self,
        probability: float,
        year_built: Optional[int],
        keywords: List[str],
        image_details: List[str],
    ) -> List[str]:
        """Schat welke onderdelen gerenoveerd moeten worden."""
        items = []
        year = year_built or 1970
        age = 2025 - year

        if probability > 0.8 or age > 50:
            items.extend(["elektra", "isolatie"])
        if probability > 0.7 or age > 40:
            items.extend(["keuken", "badkamer", "sanitair"])
        if probability > 0.5 or age > 30:
            items.extend(["schilderwerk", "vloeren"])
        if probability > 0.6 or age > 45:
            items.extend(["cv-ketel/cv-systeem"])
        if age > 55:
            items.extend(["dak", "ramen"])

        # Aanpassingen op basis van keywords
        if any(kw in keywords for kw in ["nieuwe keuken"]):
            if "keuken" not in items:
                items.append("keuken")
        if any(kw in keywords for kw in ["nieuwe badkamer"]):
            if "badkamer" not in items:
                items.append("badkamer")

        return list(set(items))

    def _build_description(
        self,
        probability: float,
        text_result: Dict,
        image_score: float,
        year_built: Optional[int],
    ) -> str:
        """Bouw een leesbare beschrijving van de klus-analyse."""
        level = (
            "zeer waarschijnlijk een kluswoning"
            if probability > 0.8
            else "waarschijnlijk renovatie nodig"
            if probability > 0.6
            else "mogelijk enige renovatie nodig"
            if probability > 0.35
            else "redelijke staat, beperkte renovatie verwacht"
        )

        parts = [f"Beoordeling: {level} ({probability:.0%})."]

        if text_result["keywords"]:
            parts.append(f"Gevonden trefwoorden: {', '.join(text_result['keywords'][:5])}.")

        if year_built:
            parts.append(f"Bouwjaar {year_built} ({2025 - year_built} jaar oud).")

        if image_score > 0:
            parts.append(f"Foto-analyse: staat score {image_score:.1f}/1.0.")

        return " ".join(parts)
