"""
Redis-based deduplication using a Bloom filter approach.
Prevents processing the same listing twice.
"""

import hashlib
import logging
from typing import List

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

BLOOM_KEY = "arbitrage:seen_listings"
BLOOM_TTL_SECONDS = 7 * 24 * 3600  # 7 days


def _listing_hash(platform: str, external_id: str) -> str:
    """Create a stable hash for a listing."""
    key = f"{platform}:{external_id}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


class ListingDeduplicator:
    """
    Fast deduplication using Redis SET.
    Checks if a listing has been seen before.

    For production at high scale, replace with RedisBloom BF.ADD/BF.EXISTS.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._client = None

    async def _get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._client

    async def is_seen(self, platform: str, external_id: str) -> bool:
        """Check if this listing was already processed."""
        client = await self._get_client()
        key = _listing_hash(platform, external_id)
        return await client.sismember(BLOOM_KEY, key)

    async def mark_seen(self, platform: str, external_id: str) -> None:
        """Mark this listing as processed."""
        client = await self._get_client()
        key = _listing_hash(platform, external_id)
        await client.sadd(BLOOM_KEY, key)
        # Refresh TTL on each write
        await client.expire(BLOOM_KEY, BLOOM_TTL_SECONDS)

    async def filter_new(self, listings: List[dict]) -> List[dict]:
        """
        Filter a list of listings to only return unseen ones.

        Args:
            listings: List of dicts with 'platform' and 'external_id' keys

        Returns:
            Subset of listings not yet seen
        """
        client = await self._get_client()
        new_listings = []

        for listing in listings:
            platform = listing.get("platform", "")
            external_id = listing.get("external_id", "")
            key = _listing_hash(platform, external_id)

            is_seen = await client.sismember(BLOOM_KEY, key)
            if not is_seen:
                new_listings.append(listing)

        logger.debug(f"Dedup: {len(new_listings)}/{len(listings)} new listings")
        return new_listings

    async def mark_batch_seen(self, listings: List[dict]) -> None:
        """Mark a batch of listings as seen in one Redis operation."""
        if not listings:
            return

        client = await self._get_client()
        keys = [
            _listing_hash(listing.get("platform", ""), listing.get("external_id", ""))
            for listing in listings
        ]

        # Pipeline for efficiency
        pipe = client.pipeline()
        for key in keys:
            pipe.sadd(BLOOM_KEY, key)
        pipe.expire(BLOOM_KEY, BLOOM_TTL_SECONDS)
        await pipe.execute()

    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.aclose()
            self._client = None
