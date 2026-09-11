from typing import Dict, Optional
import structlog

logger = structlog.get_logger()


class DealScorer:
    """
    Bereken deal score (1-100) en grade (A-F).

    Scorecomponenten:
    ┌─────────────────────────────────────┬────────┐
    │ Component                           │ Max    │
    ├─────────────────────────────────────┼────────┤
    │ ROI potentieel                      │ 30 pt  │
    │ Prijs vs WOZ                        │ 25 pt  │
    │ Prijs per m² vs buurt               │ 20 pt  │
    │ Renovatiekosten efficiëntie         │ 15 pt  │
    │ Klus-waarschijnlijkheid (upside)    │ 10 pt  │
    ├─────────────────────────────────────┼────────┤
    │ TOTAAL                              │ 100 pt │
    └─────────────────────────────────────┴────────┘
    """

    def score(
        self,
        price_ask: int,
        woz_value: Optional[int],
        neighborhood_price_per_sqm: Optional[int],
        price_per_sqm_ask: Optional[int],
        reno_cost_mid: int,
        estimated_value_after_reno: int,
        klus_probability: float,
        size_sqm: Optional[int] = None,
    ) -> Dict:
        """
        Bereken deal score en alle sub-componenten.

        Returns:
            {
                deal_score: 0-100,
                deal_grade: "A"-"F",
                score_components: {...},
                roi_percentage: float,
                potential_profit: int,
                total_investment: int,
                verdict: str,
            }
        """
        components = {}

        # ── 1. ROI potentieel (max 30 punten) ──────────────────────────────
        total_investment = price_ask + reno_cost_mid
        potential_profit = estimated_value_after_reno - total_investment
        roi_pct = (potential_profit / total_investment * 100) if total_investment > 0 else 0.0

        if roi_pct >= 30:
            components["roi"] = 30
        elif roi_pct >= 20:
            components["roi"] = 25
        elif roi_pct >= 15:
            components["roi"] = 18
        elif roi_pct >= 10:
            components["roi"] = 12
        elif roi_pct >= 5:
            components["roi"] = 7
        elif roi_pct >= 0:
            components["roi"] = 3
        else:
            components["roi"] = 0  # Verliesgevend

        # ── 2. Prijs vs WOZ waarde (max 25 punten) ─────────────────────────
        if woz_value and woz_value > 0:
            woz_ratio = price_ask / woz_value
            if woz_ratio <= 0.75:
                components["price_vs_woz"] = 25
            elif woz_ratio <= 0.85:
                components["price_vs_woz"] = 20
            elif woz_ratio <= 0.92:
                components["price_vs_woz"] = 15
            elif woz_ratio <= 1.00:
                components["price_vs_woz"] = 8
            elif woz_ratio <= 1.10:
                components["price_vs_woz"] = 3
            else:
                components["price_vs_woz"] = 0  # Boven WOZ
        else:
            components["price_vs_woz"] = 8  # Neutraal als geen WOZ data

        # ── 3. Prijs per m² vs buurt (max 20 punten) ────────────────────────
        if neighborhood_price_per_sqm and price_per_sqm_ask and neighborhood_price_per_sqm > 0:
            sqm_ratio = price_per_sqm_ask / neighborhood_price_per_sqm
            if sqm_ratio <= 0.65:
                components["price_per_sqm"] = 20
            elif sqm_ratio <= 0.75:
                components["price_per_sqm"] = 17
            elif sqm_ratio <= 0.85:
                components["price_per_sqm"] = 13
            elif sqm_ratio <= 0.95:
                components["price_per_sqm"] = 8
            elif sqm_ratio <= 1.05:
                components["price_per_sqm"] = 4
            else:
                components["price_per_sqm"] = 0
        else:
            components["price_per_sqm"] = 5  # Neutraal

        # ── 4. Renovatiekosten efficiëntie (max 15 punten) ────────────────
        # Verhouding reno_kosten / estimated_waarde (lagere ratio = beter)
        reno_ratio = reno_cost_mid / estimated_value_after_reno if estimated_value_after_reno > 0 else 1.0
        if reno_ratio <= 0.08:
            components["reno_efficiency"] = 15   # Reno < 8% van waarde
        elif reno_ratio <= 0.12:
            components["reno_efficiency"] = 12
        elif reno_ratio <= 0.18:
            components["reno_efficiency"] = 9
        elif reno_ratio <= 0.25:
            components["reno_efficiency"] = 5
        else:
            components["reno_efficiency"] = 2    # Reno > 25% van waarde

        # ── 5. Klus-upside potentieel (max 10 punten) ──────────────────────
        # Hoge klus-kans + lage vraagprijs = grote upside
        if klus_probability >= 0.8:
            components["klus_upside"] = 10
        elif klus_probability >= 0.6:
            components["klus_upside"] = 7
        elif klus_probability >= 0.4:
            components["klus_upside"] = 5
        elif klus_probability >= 0.2:
            components["klus_upside"] = 3
        else:
            components["klus_upside"] = 1

        # ── Totaal ───────────────────────────────────────────────────────────
        total_score = sum(components.values())
        total_score = max(1, min(100, total_score))

        grade = self._score_to_grade(total_score)
        verdict = self._build_verdict(total_score, roi_pct, potential_profit, grade)

        return {
            "deal_score": total_score,
            "deal_grade": grade,
            "score_components": components,
            "roi_percentage": round(roi_pct, 2),
            "potential_profit": potential_profit,
            "total_investment": total_investment,
            "verdict": verdict,
        }

    def _score_to_grade(self, score: int) -> str:
        """Converteer score naar grade."""
        if score >= 85:
            return "A"   # Uitzonderlijk goed
        elif score >= 70:
            return "B"   # Sterk
        elif score >= 55:
            return "C"   # Redelijk
        elif score >= 40:
            return "D"   # Zwak
        else:
            return "F"   # Slechte deal

    def _build_verdict(
        self, score: int, roi_pct: float, profit: int, grade: str
    ) -> str:
        """Bouw een leesbaar verdict."""
        if grade == "A":
            return f"Uitstekende deal. ROI {roi_pct:.0f}%, potentiële winst €{profit:,.0f}. Direct actie aanbevolen."
        elif grade == "B":
            return f"Goede deal. ROI {roi_pct:.0f}%, potentiële winst €{profit:,.0f}. Bezichtiging sterk aanbevolen."
        elif grade == "C":
            return f"Matige deal. ROI {roi_pct:.0f}%, potentiële winst €{profit:,.0f}. Nader onderzoek nodig."
        elif grade == "D":
            return f"Zwakke deal. ROI {roi_pct:.0f}%, marge is krap. Alleen interessant bij significante onderhandeling."
        else:
            return f"Slechte deal. ROI {roi_pct:.0f}%. Niet aanbevolen tenzij marktomstandigheden wijzigen."
