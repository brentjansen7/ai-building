"""
Alert engine — orchestrates the full deal detection and notification pipeline.

Flow:
  New listing → embed → estimate → profit calc → is_deal? → send alerts
"""

import logging
import os
from typing import Optional

import redis.asyncio as aioredis

from pipeline.embedder import EmbeddingEngine
from pipeline.price_estimator import PriceEstimator, calculate_profit, is_deal
from alerts import telegram_bot, discord_webhook
from db.database import get_session
from db.models import Estimate, AlertLog

logger = logging.getLogger(__name__)

# Dedup: don't re-alert same listing within 24h
ALERT_DEDUP_KEY = "arbitrage:alerted"
ALERT_DEDUP_TTL = 86400  # 24 hours

# Thresholds from environment (configurable without code changes)
MIN_PROFIT_EUR = float(os.getenv("MIN_PROFIT_EUR", "30"))
MIN_PROFIT_PCT = float(os.getenv("MIN_PROFIT_PCT", "0.25"))
MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.65"))


class AlertEngine:
    """
    Full pipeline: listing → embedding → estimate → profit → alert.
    Designed to be called from ARQ worker after a new listing is saved.
    """

    def __init__(self):
        self._embedder: Optional[EmbeddingEngine] = None
        self._estimator = PriceEstimator()
        self._redis: Optional[aioredis.Redis] = None

    def _get_embedder(self) -> EmbeddingEngine:
        if self._embedder is None:
            self._embedder = EmbeddingEngine()
        return self._embedder

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self._redis = await aioredis.from_url(redis_url, decode_responses=True)
        return self._redis

    async def _already_alerted(self, listing_id: int) -> bool:
        """Check if we already sent an alert for this listing."""
        redis = await self._get_redis()
        return bool(await redis.sismember(ALERT_DEDUP_KEY, str(listing_id)))

    async def _mark_alerted(self, listing_id: int) -> None:
        """Mark listing as alerted."""
        redis = await self._get_redis()
        await redis.sadd(ALERT_DEDUP_KEY, str(listing_id))
        await redis.expire(ALERT_DEDUP_KEY, ALERT_DEDUP_TTL)

    async def process_listing(self, listing: dict) -> Optional[dict]:
        """
        Full pipeline for a single listing.

        Args:
            listing: Listing dict (from DB or scraper)

        Returns:
            Result dict if a deal was found, None otherwise.
        """
        listing_id = listing.get("id")
        title = listing.get("title", "")
        description = listing.get("description", "")
        price = listing.get("price", 0)
        condition = listing.get("condition", "unknown")
        platform = listing.get("platform", "")
        category = listing.get("category")

        if not title or not price or price <= 0:
            return None

        # Skip if already alerted
        if listing_id and await self._already_alerted(listing_id):
            return None

        # Step 1: Generate embedding
        try:
            embedder = self._get_embedder()
            embedding = embedder.embed_listing(title, description)
        except Exception as e:
            logger.error(f"Embedding failed for listing {listing_id}: {e}")
            return None

        # Step 2: Estimate market value
        try:
            estimate = await self._estimator.estimate(
                title=title,
                description=description,
                condition=condition,
                platform=platform,
                embedding=embedding.tolist(),
                category=category,
            )
        except Exception as e:
            logger.error(f"Estimation failed for listing {listing_id}: {e}")
            return None

        if not estimate.get("estimated_value"):
            return None

        # Step 3: Calculate profit
        profit = calculate_profit(
            listing_price=price,
            estimated_value=estimate["estimated_value"],
            platform=platform,
        )

        # Step 4: Decide if it's a deal
        should_alert, deal_level = is_deal(
            profit_eur=profit["profit_eur"],
            profit_pct=profit["profit_pct"],
            confidence=estimate["confidence"],
            min_profit_eur=MIN_PROFIT_EUR,
            min_profit_pct=MIN_PROFIT_PCT,
            min_confidence=MIN_CONFIDENCE,
        )

        # Step 5: Save estimate to DB
        if listing_id:
            await self._save_estimate(listing_id, estimate, profit)

        if not should_alert:
            return None

        # Step 6: Send alerts
        logger.info(
            f"DEAL [{deal_level}] {title[:50]} — "
            f"€{price:.0f} → €{estimate['estimated_value']:.0f} "
            f"(+€{profit['profit_eur']:.0f}, {profit['profit_pct']:.0%})"
        )

        await self._send_alerts(listing, estimate, profit, deal_level)

        if listing_id:
            await self._mark_alerted(listing_id)

        return {
            "listing": listing,
            "estimate": estimate,
            "profit": profit,
            "deal_level": deal_level,
        }

    async def _save_estimate(
        self,
        listing_id: int,
        estimate: dict,
        profit: dict,
    ) -> None:
        """Save estimate to database."""
        async with get_session() as session:
            from sqlalchemy.dialects.postgresql import insert as pg_insert

            stmt = pg_insert(Estimate).values(
                listing_id=listing_id,
                estimated_value=estimate.get("estimated_value"),
                resale_price=profit.get("resale_price"),
                profit_score=profit.get("profit_eur"),
                profit_pct=profit.get("profit_pct"),
                confidence=estimate.get("confidence"),
                platform_fee=profit.get("platform_fee_eur"),
                shipping_est=profit.get("shipping_est"),
                comparable_count=estimate.get("comparable_count", 0),
            ).on_conflict_do_update(
                index_elements=["listing_id"],
                set_={
                    "estimated_value": estimate.get("estimated_value"),
                    "profit_score": profit.get("profit_eur"),
                    "confidence": estimate.get("confidence"),
                }
            )
            await session.execute(stmt)

    async def _send_alerts(
        self,
        listing: dict,
        estimate: dict,
        profit: dict,
        deal_level: str,
    ) -> None:
        """Send to all configured notification channels."""
        # Telegram
        tg_ok = await telegram_bot.send_deal_alert(listing, estimate, profit, deal_level)

        # Discord
        dc_ok = await discord_webhook.send_deal_alert(listing, estimate, profit, deal_level)

        # Log to DB
        listing_id = listing.get("id")
        if listing_id:
            async with get_session() as session:
                channels = []
                if tg_ok:
                    channels.append("telegram")
                if dc_ok:
                    channels.append("discord")

                for channel in channels:
                    log = AlertLog(
                        listing_id=listing_id,
                        channel=channel,
                        profit_at_send=profit.get("profit_eur"),
                    )
                    session.add(log)

    async def close(self):
        """Cleanup resources."""
        if self._redis:
            await self._redis.aclose()
