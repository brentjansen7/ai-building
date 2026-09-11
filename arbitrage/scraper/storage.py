"""
Database storage layer for scraped listings.
Handles upserts, deduplication, and batch inserts.
"""

import logging
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, update, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from db.database import get_session
from db.models import Listing, SoldListing, ScraperRun, PriceHistory

logger = logging.getLogger(__name__)


async def save_listings(
    raw_listings: List[dict],
    run_id: Optional[int] = None,
) -> tuple[int, int]:
    """
    Upsert scraped listings into the database.

    Args:
        raw_listings: List of listing dicts from scrapers
        run_id: Optional scraper run ID for tracking

    Returns:
        (total, new) count tuple
    """
    if not raw_listings:
        return 0, 0

    total = len(raw_listings)
    new_count = 0

    async with get_session() as session:
        for listing_data in raw_listings:
            try:
                # Build upsert statement
                stmt = pg_insert(Listing).values(
                    platform=listing_data["platform"],
                    external_id=listing_data["external_id"],
                    title=listing_data["title"],
                    description=listing_data.get("description", ""),
                    price=listing_data["price"],
                    condition=listing_data.get("condition"),
                    category=listing_data.get("category"),
                    brand=listing_data.get("brand"),
                    seller_id=listing_data.get("seller_id"),
                    location=listing_data.get("location"),
                    url=listing_data["url"],
                    image_urls=listing_data.get("image_urls", []),
                    posted_at=listing_data.get("posted_at"),
                    scraped_at=datetime.utcnow(),
                    metadata=listing_data.get("metadata", {}),
                )

                # On conflict: update price and scraped_at
                stmt = stmt.on_conflict_do_update(
                    constraint="uq_listing_platform_external",
                    set_={
                        "price": stmt.excluded.price,
                        "scraped_at": stmt.excluded.scraped_at,
                        "description": stmt.excluded.description,
                        "image_urls": stmt.excluded.image_urls,
                        "metadata": stmt.excluded.metadata,
                    },
                ).returning(Listing.id, Listing.scraped_at)

                result = await session.execute(stmt)
                row = result.fetchone()

                if row:
                    new_count += 1

                    # Track price history for auction items
                    if listing_data.get("metadata", {}).get("auction_house"):
                        price_entry = PriceHistory(
                            listing_id=row[0],
                            price=listing_data["price"],
                            observed_at=datetime.utcnow(),
                        )
                        session.add(price_entry)

            except Exception as e:
                logger.warning(f"Failed to save listing {listing_data.get('external_id')}: {e}")
                continue

        # Update scraper run stats
        if run_id:
            await session.execute(
                update(ScraperRun)
                .where(ScraperRun.id == run_id)
                .values(
                    listings_found=total,
                    listings_new=new_count,
                )
            )

    logger.info(f"Saved {new_count}/{total} new listings to database")
    return total, new_count


async def start_scraper_run(platform: str) -> int:
    """Create a new scraper run record and return its ID."""
    async with get_session() as session:
        run = ScraperRun(platform=platform, started_at=datetime.utcnow())
        session.add(run)
        await session.flush()
        return run.id


async def finish_scraper_run(
    run_id: int,
    status: str = "completed",
    error: Optional[str] = None,
) -> None:
    """Mark a scraper run as finished."""
    async with get_session() as session:
        await session.execute(
            update(ScraperRun)
            .where(ScraperRun.id == run_id)
            .values(
                completed_at=datetime.utcnow(),
                status=status,
                error_message=error,
            )
        )


async def get_listings_without_embeddings(
    platform: Optional[str] = None,
    limit: int = 100,
) -> List[dict]:
    """Get listings that don't have embeddings yet (for embedding worker)."""
    async with get_session() as session:
        query = (
            select(Listing.id, Listing.title, Listing.description)
            .where(Listing.embedding.is_(None))
        )

        if platform:
            query = query.where(Listing.platform == platform)

        query = query.order_by(Listing.scraped_at.desc()).limit(limit)

        result = await session.execute(query)
        return [
            {"id": row.id, "title": row.title, "description": row.description}
            for row in result.fetchall()
        ]


async def save_embedding(listing_id: int, embedding: list) -> None:
    """Save embedding vector to a listing."""
    async with get_session() as session:
        await session.execute(
            update(Listing)
            .where(Listing.id == listing_id)
            .values(embedding=embedding)
        )


async def get_platform_stats() -> List[dict]:
    """Get current stats per platform for monitoring."""
    async with get_session() as session:
        result = await session.execute(
            select(
                Listing.platform,
                func.count(Listing.id).label("total"),
                func.count(Listing.embedding).label("embedded"),
                func.max(Listing.scraped_at).label("last_scraped"),
            )
            .group_by(Listing.platform)
        )

        return [
            {
                "platform": row.platform,
                "total": row.total,
                "embedded": row.embedded,
                "pending_embedding": row.total - row.embedded,
                "last_scraped": row.last_scraped.isoformat() if row.last_scraped else None,
            }
            for row in result.fetchall()
        ]
