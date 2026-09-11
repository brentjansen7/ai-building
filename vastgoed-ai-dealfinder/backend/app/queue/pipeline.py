"""
Pipeline: coördineert het volledige analyse-proces voor één listing.
"""
import asyncio
from typing import Dict, Optional, List
from datetime import datetime
import structlog

from app.database import AsyncSessionLocal
from app.models.db import Listing, Analysis
from app.config import settings
from sqlalchemy import select

logger = structlog.get_logger()


async def save_listings(listings: List[Dict]) -> int:
    """Sla nieuwe listings op in de database."""
    saved = 0
    async with AsyncSessionLocal() as db:
        for data in listings:
            try:
                # Check of listing al bestaat
                existing = await db.execute(
                    select(Listing).where(Listing.source_id == data["source_id"])
                )
                if existing.scalar_one_or_none():
                    continue  # Skip duplicaat

                listing = Listing(
                    source=data.get("source"),
                    source_id=data.get("source_id"),
                    url=data.get("url"),
                    title=data.get("title", ""),
                    price_ask=data.get("price_ask"),
                    address=data.get("address", ""),
                    city=data.get("city", ""),
                    postcode=data.get("postcode"),
                    size_sqm=data.get("size_sqm"),
                    rooms=data.get("rooms"),
                    bedrooms=data.get("bedrooms"),
                    year_built=data.get("year_built"),
                    property_type=data.get("property_type"),
                    energy_label=data.get("energy_label"),
                    description=data.get("description"),
                    image_urls=data.get("image_urls", []),
                    images_count=data.get("images_count", 0),
                    analysis_status="pending",
                )
                db.add(listing)
                saved += 1
            except Exception as e:
                logger.error("Listing opslaan fout", error=str(e))
                continue

        await db.commit()
    return saved


async def run_full_analysis(listing_id: str) -> Dict:
    """
    Volledige analyse pipeline voor één listing:
    1. Haal listing op uit DB
    2. WOZ data ophalen
    3. Klus detectie
    4. Renovatiekosten schatten
    5. Marktwaarde berekenen
    6. Deal score berekenen
    7. Resultaten opslaan
    """
    from app.scrapers.woz_fetcher import WOZFetcher
    from app.services.klus_detector import KlusDetector
    from app.services.renovation_cost import RenovationCostEstimator
    from app.services.market_value import MarketValuationEngine
    from app.services.deal_scorer import DealScorer

    async with AsyncSessionLocal() as db:
        # 1. Haal listing op
        result = await db.execute(select(Listing).where(Listing.id == listing_id))
        listing = result.scalar_one_or_none()

        if not listing:
            logger.error("Listing niet gevonden", listing_id=listing_id)
            return {"error": "not_found"}

        # Update status naar 'analyzing'
        listing.analysis_status = "analyzing"
        await db.commit()

        try:
            # 2. WOZ data
            if not listing.woz_value and listing.postcode:
                woz_fetcher = WOZFetcher()
                woz_data = await woz_fetcher.get_woz(listing.address, listing.postcode)
                if woz_data:
                    listing.woz_value = woz_data.get("woz_value")
                    listing.woz_year = woz_data.get("woz_year")

            # 3. Klus detectie
            klus_detector = KlusDetector(settings.anthropic_api_key)
            klus_result = await klus_detector.analyze(
                description=listing.description,
                title=listing.title,
                image_urls=listing.image_urls,
                year_built=listing.year_built,
            )
            listing.is_klus_likely = klus_result["klus_probability"] >= 0.4
            listing.klus_confidence = klus_result["klus_probability"]
            listing.klus_keywords = klus_result["klus_keywords"]

            # 4. Renovatiekosten
            reno_estimator = RenovationCostEstimator()
            reno_result = reno_estimator.estimate_from_probability(
                klus_probability=klus_result["klus_probability"],
                size_sqm=listing.size_sqm or 80,
                year_built=listing.year_built,
                city=listing.city,
            )

            # 5. Marktwaarde
            valuation_engine = MarketValuationEngine(db)
            valuation_result = await valuation_engine.estimate(
                price_ask=listing.price_ask or 0,
                size_sqm=listing.size_sqm or 80,
                city=listing.city,
                postcode=listing.postcode,
                woz_value=listing.woz_value,
                year_built=listing.year_built,
                rooms=listing.rooms,
                klus_probability=klus_result["klus_probability"],
                reno_cost_mid=reno_result["cost_mid"],
            )

            # 6. Deal score
            scorer = DealScorer()
            score_result = scorer.score(
                price_ask=listing.price_ask or 0,
                woz_value=listing.woz_value,
                neighborhood_price_per_sqm=valuation_result["neighborhood_price_per_sqm"],
                price_per_sqm_ask=valuation_result["price_per_sqm_ask"],
                reno_cost_mid=reno_result["cost_mid"],
                estimated_value_after_reno=valuation_result["estimated_value_after_reno"],
                klus_probability=klus_result["klus_probability"],
                size_sqm=listing.size_sqm,
            )

            # 7. Opslaan
            analysis = Analysis(
                listing_id=listing.id,
                klus_probability=klus_result["klus_probability"],
                klus_description=klus_result["description"],
                reno_cost_min=reno_result["cost_min"],
                reno_cost_mid=reno_result["cost_mid"],
                reno_cost_max=reno_result["cost_max"],
                reno_breakdown=reno_result["breakdown_mid"],
                estimated_value_after_reno=valuation_result["estimated_value_after_reno"],
                market_value_comparable=valuation_result["estimated_current_value"],
                price_per_sqm=valuation_result["price_per_sqm_ask"],
                neighborhood_price_per_sqm=valuation_result["neighborhood_price_per_sqm"],
                total_investment=score_result["total_investment"],
                potential_profit=score_result["potential_profit"],
                roi_percentage=score_result["roi_percentage"],
                deal_score=score_result["deal_score"],
                deal_grade=score_result["deal_grade"],
                score_components=score_result["score_components"],
                model_version="1.0",
                analyzed_by="pipeline",
            )
            db.add(analysis)

            listing.analysis_status = "done"
            listing.analyzed_at = datetime.now()
            await db.commit()

            logger.info(
                "Analyse klaar",
                listing_id=listing_id,
                score=score_result["deal_score"],
                grade=score_result["deal_grade"],
                profit=score_result["potential_profit"],
            )

            return {
                "listing_id": listing_id,
                "deal_score": score_result["deal_score"],
                "deal_grade": score_result["deal_grade"],
                "potential_profit": score_result["potential_profit"],
                "roi_percentage": score_result["roi_percentage"],
            }

        except Exception as e:
            logger.error("Analyse fout", listing_id=listing_id, error=str(e))
            listing.analysis_status = "failed"
            await db.commit()
            return {"error": str(e)}
