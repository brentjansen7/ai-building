"""
Discord alert delivery via webhook.
Sends deal alerts as rich embeds with color coding by deal level.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# Color by deal level (Discord embed colors as decimal)
DEAL_COLORS = {
    "EXCELLENT": 0x22C55E,  # Green
    "GOOD":      0xF59E0B,  # Amber
    "FAIR":      0x3B82F6,  # Blue
}

DEAL_EMOJI = {"EXCELLENT": "🔥", "GOOD": "✅", "FAIR": "📊"}


def _build_embed(
    listing: dict,
    estimate: dict,
    profit: dict,
    deal_level: str,
) -> dict:
    """Build a Discord embed object for a deal alert."""
    title = listing.get("title", "")[:100]
    platform = listing.get("platform", "").title()
    price = listing.get("price", 0)
    est_value = estimate.get("estimated_value") or 0
    resale_price = profit.get("resale_price", 0)
    profit_eur = profit.get("profit_eur", 0)
    profit_pct = profit.get("profit_pct", 0)
    confidence = estimate.get("confidence", 0)
    category = listing.get("category", "—")
    url = listing.get("url", "")
    image_urls = listing.get("image_urls", [])

    emoji = DEAL_EMOJI.get(deal_level, "📢")
    color = DEAL_COLORS.get(deal_level, 0x6B7280)

    embed = {
        "title": f"{emoji} {title}",
        "url": url,
        "color": color,
        "fields": [
            {"name": "💰 Vraagprijs", "value": f"€{price:.0f}", "inline": True},
            {"name": "📈 Marktwaarde", "value": f"€{est_value:.0f}", "inline": True},
            {"name": "💵 Winst", "value": f"€{profit_eur:.0f} ({profit_pct:.0%})", "inline": True},
            {"name": "🎯 Betrouwbaarheid", "value": f"{confidence:.0%}", "inline": True},
            {"name": "🏷️ Categorie", "value": category, "inline": True},
            {"name": "🛒 Platform", "value": platform, "inline": True},
        ],
        "footer": {
            "text": f"AI Arbitrage • {deal_level}",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Add thumbnail if image available
    if image_urls:
        embed["thumbnail"] = {"url": image_urls[0]}

    return embed


async def send_deal_alert(
    listing: dict,
    estimate: dict,
    profit: dict,
    deal_level: str,
) -> bool:
    """
    Send a deal alert to Discord via webhook.

    Returns True if sent successfully.
    """
    if not DISCORD_WEBHOOK_URL:
        logger.warning("Discord not configured (DISCORD_WEBHOOK_URL missing)")
        return False

    try:
        embed = _build_embed(listing, estimate, profit, deal_level)
        emoji = DEAL_EMOJI.get(deal_level, "")
        profit_eur = profit.get("profit_eur", 0)

        payload = {
            "content": f"{emoji} **{deal_level} deal gevonden** — €{profit_eur:.0f} winst potentieel",
            "embeds": [embed],
        }

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                DISCORD_WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()

        logger.info(f"Discord alert sent: {listing.get('title', '')[:40]} — €{profit_eur:.0f}")
        return True

    except Exception as e:
        logger.error(f"Discord send failed: {e}")
        return False
