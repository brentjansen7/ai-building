"""
ARQ task definitions — the scraper job queue.

Workers run continuously and pick up tasks from Redis queues.
Each platform gets its own queue to allow independent scaling and rate limiting.

Start workers with:
  arq scraper.tasks.WorkerSettings
  arq scraper.tasks.EmbeddingWorkerSettings
  arq scraper.tasks.AlertWorkerSettings
"""

import logging
import os
from typing import Any

from arq import cron
from arq.connections import RedisSettings

from scraper.platforms.marktplaats import MarktplaatsScraper
from scraper.platforms.auctionet import scrape_auctionet_open
from scraper.platforms.bva_auctions import scrape_bva_auctions
from scraper.platforms.vinted import VintedScraper
from scraper.platforms.ebay import EbayFindingAPIScraper, import_ebay_sold_data
from scraper.storage import save_listings, start_scraper_run, finish_scraper_run, get_listings_without_embeddings
from scraper.dedup import ListingDeduplicator

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_dedup = ListingDeduplicator(REDIS_URL)


# ─── SCRAPER TASKS ───────────────────────────────────────────────────────────

async def task_scrape_marktplaats(ctx: dict) -> dict:
    """Scrape Marktplaats for new listings."""
    run_id = await start_scraper_run("marktplaats")
    try:
        scraper = MarktplaatsScraper()
        raw = await scraper.fetch_listings()
        await scraper.close()

        new_listings = await _dedup.filter_new(raw)
        total, new = await save_listings(new_listings, run_id=run_id)
        await _dedup.mark_batch_seen(new_listings)

        # Enqueue embedding + alert tasks for new listings
        for listing in new_listings[:50]:  # Cap to avoid queue flooding
            await ctx["redis"].enqueue_job("task_process_listing", listing)

        await finish_scraper_run(run_id)
        logger.info(f"[marktplaats] {new}/{total} new listings queued")
        return {"platform": "marktplaats", "total": total, "new": new}

    except Exception as e:
        await finish_scraper_run(run_id, status="failed", error=str(e))
        logger.error(f"[marktplaats] Scrape failed: {e}")
        raise


async def task_scrape_auctionet(ctx: dict) -> dict:
    """Scrape Auctionet for open lots."""
    run_id = await start_scraper_run("auctionet")
    try:
        raw = await scrape_auctionet_open()

        new_listings = await _dedup.filter_new(raw)
        total, new = await save_listings(new_listings, run_id=run_id)
        await _dedup.mark_batch_seen(new_listings)

        for listing in new_listings[:50]:
            await ctx["redis"].enqueue_job("task_process_listing", listing)

        await finish_scraper_run(run_id)
        logger.info(f"[auctionet] {new}/{total} new lots queued")
        return {"platform": "auctionet", "total": total, "new": new}

    except Exception as e:
        await finish_scraper_run(run_id, status="failed", error=str(e))
        logger.error(f"[auctionet] Scrape failed: {e}")
        raise


async def task_scrape_vinted(ctx: dict) -> dict:
    """Scrape Vinted for new listings."""
    run_id = await start_scraper_run("vinted")
    try:
        scraper = VintedScraper()
        raw = await scraper.fetch_listings()
        await scraper.close()

        new_listings = await _dedup.filter_new(raw)
        total, new = await save_listings(new_listings, run_id=run_id)
        await _dedup.mark_batch_seen(new_listings)

        for listing in new_listings[:50]:
            await ctx["redis"].enqueue_job("task_process_listing", listing)

        await finish_scraper_run(run_id)
        logger.info(f"[vinted] {new}/{total} new listings queued")
        return {"platform": "vinted", "total": total, "new": new}

    except Exception as e:
        await finish_scraper_run(run_id, status="failed", error=str(e))
        logger.error(f"[vinted] Scrape failed: {e}")
        raise


async def task_scrape_ebay(ctx: dict) -> dict:
    """Scrape eBay active listings + import sold data."""
    run_id = await start_scraper_run("ebay")
    try:
        scraper = EbayFindingAPIScraper()
        raw = await scraper.fetch_listings()
        await scraper.close()

        new_listings = await _dedup.filter_new(raw)
        total, new = await save_listings(new_listings, run_id=run_id)
        await _dedup.mark_batch_seen(new_listings)

        for listing in new_listings[:30]:
            await ctx["redis"].enqueue_job("task_process_listing", listing)

        await finish_scraper_run(run_id)
        logger.info(f"[ebay] {new}/{total} new listings queued")
        return {"platform": "ebay", "total": total, "new": new}

    except Exception as e:
        await finish_scraper_run(run_id, status="failed", error=str(e))
        logger.error(f"[ebay] Scrape failed: {e}")
        raise


async def task_import_ebay_sold(ctx: dict) -> dict:
    """Import eBay sold/completed listings for price reference data."""
    try:
        count = await import_ebay_sold_data()
        logger.info(f"[ebay_sold] Imported {count} sold listings")
        return {"imported": count}
    except Exception as e:
        logger.error(f"[ebay_sold] Import failed: {e}")
        raise


async def task_scrape_bva(ctx: dict) -> dict:
    """Scrape BVA Auctions for active lots."""
    run_id = await start_scraper_run("bva_auctions")
    try:
        raw = await scrape_bva_auctions()

        new_listings = await _dedup.filter_new(raw)
        total, new = await save_listings(new_listings, run_id=run_id)
        await _dedup.mark_batch_seen(new_listings)

        for listing in new_listings[:50]:
            await ctx["redis"].enqueue_job("task_process_listing", listing)

        await finish_scraper_run(run_id)
        logger.info(f"[bva_auctions] {new}/{total} new lots queued")
        return {"platform": "bva_auctions", "total": total, "new": new}

    except Exception as e:
        await finish_scraper_run(run_id, status="failed", error=str(e))
        logger.error(f"[bva_auctions] Scrape failed: {e}")
        raise


# ─── PROCESSING TASK (embedding + alert) ─────────────────────────────────────

async def task_process_listing(ctx: dict, listing: dict) -> dict:
    """
    Full pipeline for a single new listing:
    1. Generate embedding
    2. Estimate price
    3. Calculate profit
    4. Send alert if deal found
    """
    from alerts.alert_engine import AlertEngine

    engine = AlertEngine()
    try:
        result = await engine.process_listing(listing)
        if result:
            logger.info(
                f"Deal found: {listing.get('title', '')[:40]} "
                f"— {result['deal_level']} "
                f"€{result['profit']['profit_eur']:.0f}"
            )
        return {"processed": True, "deal_found": result is not None}
    except Exception as e:
        logger.error(f"Processing failed for listing {listing.get('id')}: {e}")
        return {"processed": False, "error": str(e)}
    finally:
        await engine.close()


# ─── BATCH EMBEDDING TASK (for historical listings) ──────────────────────────

async def task_embed_pending(ctx: dict) -> dict:
    """
    Embed all listings that don't have embeddings yet.
    Runs as a background task to catch up after scraper runs.
    """
    from pipeline.embedder import BatchEmbedder
    from scraper.storage import save_embedding

    pending = await get_listings_without_embeddings(limit=200)

    if not pending:
        return {"embedded": 0}

    embedder = BatchEmbedder()
    pairs = embedder.embed_and_return(pending)

    count = 0
    for listing_id, embedding in pairs:
        try:
            await save_embedding(listing_id, embedding)
            count += 1
        except Exception as e:
            logger.error(f"Failed to save embedding {listing_id}: {e}")

    logger.info(f"Embedded {count}/{len(pending)} pending listings")
    return {"embedded": count}


# ─── NICHE DISCOVERY TASK ────────────────────────────────────────────────────

async def task_niche_discovery(ctx: dict) -> dict:
    """
    Weekly: analyze which categories have highest profit margins.
    Updates niche_performance table.
    """
    from db.database import get_session
    from sqlalchemy import text

    async with get_session() as session:
        result = await session.execute(text("""
            INSERT INTO niche_performance (category, platform, avg_margin, deal_count, updated_at)
            SELECT
                l.category,
                l.platform,
                AVG(e.profit_score) as avg_margin,
                COUNT(*) as deal_count,
                NOW()
            FROM estimates e
            JOIN listings l ON l.id = e.listing_id
            WHERE e.created_at > NOW() - INTERVAL '30 days'
              AND e.profit_score > 0
              AND l.category IS NOT NULL
            GROUP BY l.category, l.platform
            ON CONFLICT (category, platform)
            DO UPDATE SET
                avg_margin = EXCLUDED.avg_margin,
                deal_count = EXCLUDED.deal_count,
                updated_at = NOW()
        """))

    logger.info("Niche performance table updated")
    return {"status": "ok"}


# ─── WORKER SETTINGS ─────────────────────────────────────────────────────────

async def startup(ctx: dict):
    """Worker startup — log and send system message."""
    logger.info("ARQ worker starting up")
    try:
        from alerts.telegram_bot import send_system_message
        await send_system_message("Arbitrage worker gestart ✅")
    except Exception:
        pass


async def shutdown(ctx: dict):
    """Worker shutdown cleanup."""
    logger.info("ARQ worker shutting down")
    await _dedup.close()


class WorkerSettings:
    """Main scraper worker — runs all platform scrapers on schedule."""

    redis_settings = RedisSettings.from_dsn(REDIS_URL)

    functions = [
        task_scrape_marktplaats,
        task_scrape_vinted,
        task_scrape_ebay,
        task_scrape_auctionet,
        task_scrape_bva,
        task_import_ebay_sold,
        task_process_listing,
        task_embed_pending,
        task_niche_discovery,
    ]

    # Cron schedule: scrape every N minutes
    cron_jobs = [
        cron(task_scrape_marktplaats, minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}),  # every 5 min
        cron(task_scrape_vinted, minute={0, 10, 20, 30, 40, 50}),     # every 10 min
        cron(task_scrape_ebay, minute={0, 20, 40}),                    # every 20 min
        cron(task_scrape_auctionet, minute={0, 10, 20, 30, 40, 50}),  # every 10 min
        cron(task_scrape_bva, minute={0, 15, 30, 45}),                 # every 15 min
        cron(task_import_ebay_sold, hour=2, minute=0),                 # Daily 2am
        cron(task_embed_pending, minute={2, 17, 32, 47}),              # every 15 min, offset
        cron(task_niche_discovery, weekday=0, hour=3, minute=0),       # Monday 3am
    ]

    max_jobs = 20
    job_timeout = 120  # 2 minutes max per job
    keep_result = 300  # Keep job results 5 minutes

    on_startup = startup
    on_shutdown = shutdown
