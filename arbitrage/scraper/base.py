"""
Base scraper class - all platform scrapers inherit from this.
Handles proxy rotation, rate limiting, retries, and logging.
"""

import asyncio
import logging
import random
import os
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

import curl_cffi.requests as cffi_requests

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter for per-scraper rate control."""

    def __init__(self, requests_per_minute: int):
        self.rate = requests_per_minute / 60.0  # requests per second
        self.tokens = float(requests_per_minute)
        self.max_tokens = float(requests_per_minute)
        self.last_update = asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0.0

    async def acquire(self):
        """Wait until a request token is available."""
        try:
            now = asyncio.get_event_loop().time()
        except RuntimeError:
            return

        elapsed = now - self.last_update
        self.tokens = min(self.max_tokens, self.tokens + elapsed * self.rate)
        self.last_update = now

        if self.tokens < 1.0:
            wait_time = (1.0 - self.tokens) / self.rate
            await asyncio.sleep(wait_time)
            self.tokens = 0.0
        else:
            self.tokens -= 1.0


class ProxyPool:
    """
    Rotating proxy pool. Reads proxies from PROXY_LIST env variable.
    Format: "http://user:pass@host:port,http://user:pass@host2:port2"

    For production: integrate Bright Data / Smartproxy API for dynamic pools.
    """

    def __init__(self):
        proxy_list = os.getenv("PROXY_LIST", "")
        if proxy_list:
            self.proxies = [p.strip() for p in proxy_list.split(",") if p.strip()]
        else:
            self.proxies = []
        self._index = 0

    def get(self) -> Optional[str]:
        """Get next proxy in round-robin rotation."""
        if not self.proxies:
            return None
        proxy = self.proxies[self._index % len(self.proxies)]
        self._index += 1
        return proxy

    def has_proxies(self) -> bool:
        return len(self.proxies) > 0


# Shared proxy pool instance
_proxy_pool = ProxyPool()


class BaseScraper(ABC):
    """
    Abstract base class for all platform scrapers.

    Subclasses must implement:
        - platform: str property
        - requests_per_minute: int property
        - fetch_listings(): async generator of raw listing dicts
    """

    BROWSER_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/html, */*",
        "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "DNT": "1",
    }

    MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 2.0  # seconds

    def __init__(self):
        self._rate_limiter: Optional[RateLimiter] = None
        self._session: Optional[cffi_requests.AsyncSession] = None
        self._proxy_pool = _proxy_pool

    @property
    @abstractmethod
    def platform(self) -> str:
        """Platform identifier, e.g. 'marktplaats'"""
        pass

    @property
    @abstractmethod
    def requests_per_minute(self) -> int:
        """Max requests per minute for this platform."""
        pass

    @abstractmethod
    async def fetch_listings(self) -> List[dict]:
        """
        Fetch new listings from the platform.
        Returns list of normalized listing dicts.
        """
        pass

    async def _get_session(self) -> cffi_requests.AsyncSession:
        """Get or create a curl-cffi session (Chrome TLS fingerprint)."""
        if self._session is None:
            proxy = self._proxy_pool.get()
            self._session = cffi_requests.AsyncSession(
                impersonate="chrome124",
                headers=self.BROWSER_HEADERS,
                proxies={"https": proxy, "http": proxy} if proxy else None,
                timeout=15,
            )
        return self._session

    async def _rate_limit(self):
        """Apply rate limiting before each request."""
        if self._rate_limiter is None:
            self._rate_limiter = RateLimiter(self.requests_per_minute)
        await self._rate_limiter.acquire()

    async def get(self, url: str, **kwargs) -> cffi_requests.Response:
        """
        Rate-limited GET with automatic retries and proxy rotation.
        Raises on final failure.
        """
        for attempt in range(self.MAX_RETRIES):
            await self._rate_limit()

            # Random jitter to appear human
            await asyncio.sleep(random.uniform(0.5, 2.0))

            try:
                session = await self._get_session()
                response = await session.get(url, **kwargs)

                if response.status_code == 429:
                    wait = self.RETRY_BACKOFF_BASE ** (attempt + 2)
                    logger.warning(f"[{self.platform}] Rate limited. Waiting {wait}s")
                    await asyncio.sleep(wait)
                    self._session = None  # Rotate proxy on next request
                    continue

                if response.status_code == 403:
                    logger.warning(f"[{self.platform}] 403 Forbidden on {url} - rotating proxy")
                    self._session = None
                    await asyncio.sleep(self.RETRY_BACKOFF_BASE ** attempt)
                    continue

                response.raise_for_status()
                return response

            except Exception as e:
                wait = self.RETRY_BACKOFF_BASE ** attempt
                logger.warning(f"[{self.platform}] Request failed (attempt {attempt+1}): {e}. Retrying in {wait}s")
                self._session = None
                if attempt == self.MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(wait)

    def normalize_condition(self, raw: str) -> str:
        """Map platform-specific condition strings to normalized values."""
        raw = raw.lower().strip() if raw else ""
        if any(w in raw for w in ["nieuw", "new", "nieuw in doos"]):
            return "new"
        if any(w in raw for w in ["zo goed als nieuw", "als nieuw", "like new", "mint"]):
            return "like_new"
        if any(w in raw for w in ["goed", "good", "gebruikt"]):
            return "good"
        if any(w in raw for w in ["redelijk", "fair", "lichte gebruikssp"]):
            return "fair"
        if any(w in raw for w in ["slecht", "poor", "beschadigd", "defect"]):
            return "poor"
        return "good"  # default

    async def close(self):
        """Close the HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
