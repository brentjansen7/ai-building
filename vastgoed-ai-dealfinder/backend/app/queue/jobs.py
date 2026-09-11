"""
RQ Job Functies — worden uitgevoerd door workers.
Alle functies zijn synchrone wrappers om asyncio te ondersteunen.
"""
import asyncio
from typing import Optional, Dict
import structlog

logger = structlog.get_logger()


def _run(coro):
    """Helper om async coroutines te runnen in sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ─────────────────────────────────────────────────────────────────────────────
# SCRAPE JOBS
# ─────────────────────────────────────────────────────────────────────────────

def scrape_pararius(max_pages: int = 10):
    """Scrape Pararius voor nieuwe listings."""
    return _run(_scrape_pararius_async(max_pages))


async def _scrape_pararius_async(max_pages: int):
    from app.scrapers.pararius import ParariusScraper
    from app.config import settings
    from app.queue.pipeline import save_listings

    scraper = ParariusScraper(proxy_list=settings.proxy_list_parsed)
    listings = await scraper.scrape_all(max_pages=max_pages)
    saved = await save_listings(listings)
    logger.info("Pararius scrape klaar", total=len(listings), saved=saved)
    return {"source": "pararius", "scraped": len(listings), "saved": saved}


def scrape_jaap(max_pages: int = 10):
    """Scrape Jaap.nl voor nieuwe listings."""
    return _run(_scrape_jaap_async(max_pages))


async def _scrape_jaap_async(max_pages: int):
    from app.scrapers.jaap import JaapScraper
    from app.config import settings
    from app.queue.pipeline import save_listings

    scraper = JaapScraper(proxy_list=settings.proxy_list_parsed)
    listings = await scraper.scrape_all(max_pages=max_pages)
    saved = await save_listings(listings)
    logger.info("Jaap scrape klaar", total=len(listings), saved=saved)
    return {"source": "jaap", "scraped": len(listings), "saved": saved}


def scrape_huislijn(max_pages: int = 10):
    """Scrape Huislijn.nl voor nieuwe listings."""
    return _run(_scrape_huislijn_async(max_pages))


async def _scrape_huislijn_async(max_pages: int):
    from app.scrapers.huislijn import HuislijnScraper
    from app.config import settings
    from app.queue.pipeline import save_listings

    scraper = HuislijnScraper(proxy_list=settings.proxy_list_parsed)
    listings = await scraper.scrape_all(max_pages=max_pages)
    saved = await save_listings(listings)
    logger.info("Huislijn scrape klaar", total=len(listings), saved=saved)
    return {"source": "huislijn", "scraped": len(listings), "saved": saved}


# ─────────────────────────────────────────────────────────────────────────────
# ANALYSE JOBS
# ─────────────────────────────────────────────────────────────────────────────

def analyze_listing(listing_id: str):
    """Analyseer één listing volledig."""
    return _run(_analyze_listing_async(listing_id))


async def _analyze_listing_async(listing_id: str):
    from app.queue.pipeline import run_full_analysis
    return await run_full_analysis(listing_id)


def analyze_pending_listings(limit: int = 50):
    """Analyseer alle listings met status 'pending'."""
    return _run(_analyze_pending_async(limit))


async def _analyze_pending_async(limit: int):
    from app.database import AsyncSessionLocal
    from app.models.db import Listing
    from app.queue.pipeline import run_full_analysis
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Listing)
            .where(Listing.analysis_status == "pending")
            .limit(limit)
        )
        listings = result.scalars().all()

    logger.info("Analyseer pending listings", count=len(listings))
    results = []
    for listing in listings:
        try:
            result = await run_full_analysis(str(listing.id))
            results.append(result)
        except Exception as e:
            logger.error("Analyse fout", listing_id=str(listing.id), error=str(e))

    return {"analyzed": len(results)}


# ─────────────────────────────────────────────────────────────────────────────
# ALERT JOBS
# ─────────────────────────────────────────────────────────────────────────────

def check_and_send_alerts():
    """Controleer op nieuwe hoge-score deals en stuur alerts."""
    return _run(_check_alerts_async())


async def _check_alerts_async():
    from app.database import AsyncSessionLocal
    from app.models.db import Analysis, Listing, Alert
    from app.services.alert_service import AlertService
    from app.config import settings
    from sqlalchemy import select, and_, not_, exists
    from datetime import datetime, timedelta

    alert_service = AlertService()
    sent_count = 0

    async with AsyncSessionLocal() as db:
        # Haal hoge-score analyses op die nog geen alert hebben
        cutoff = datetime.now() - timedelta(hours=24)
        result = await db.execute(
            select(Analysis, Listing)
            .join(Listing)
            .where(
                and_(
                    Analysis.deal_score >= settings.min_deal_score,
                    Analysis.deal_grade.in_(settings.alert_grades_list),
                    Analysis.roi_percentage >= settings.min_roi_percentage,
                    Analysis.potential_profit >= settings.min_profit,
                    Analysis.created_at >= cutoff,
                    ~exists(
                        select(Alert.id).where(Alert.analysis_id == Analysis.id)
                    ),
                )
            )
            .limit(10)
        )

        rows = result.all()
        logger.info("Deals gevonden voor alert", count=len(rows))

        for analysis, listing in rows:
            listing_dict = {
                "id": str(listing.id),
                "address": listing.address,
                "city": listing.city,
                "price_ask": listing.price_ask,
                "woz_value": listing.woz_value,
                "url": listing.url,
                "is_klus_likely": listing.is_klus_likely,
                "klus_confidence": listing.klus_confidence,
            }
            analysis_dict = {
                "deal_grade": analysis.deal_grade,
                "deal_score": analysis.deal_score,
                "potential_profit": analysis.potential_profit,
                "roi_percentage": analysis.roi_percentage,
                "reno_cost_mid": analysis.reno_cost_mid,
                "estimated_value_after_reno": analysis.estimated_value_after_reno,
                "verdict": "",
            }

            results = await alert_service.send_all(listing_dict, analysis_dict)

            # Sla alert op in DB
            for channel, success in results.items():
                alert = Alert(
                    listing_id=listing.id,
                    analysis_id=analysis.id,
                    alert_type=channel,
                    deal_grade=analysis.deal_grade,
                    deal_score=analysis.deal_score,
                    success=success,
                )
                db.add(alert)
                if success:
                    sent_count += 1

        await db.commit()

    logger.info("Alerts verstuurd", count=sent_count)
    return {"alerts_sent": sent_count}
