"""
Telegram alert delivery via aiogram.
Sends deal alerts with inline keyboard (View Listing button).
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

DEAL_EMOJI = {"EXCELLENT": "🔥", "GOOD": "✅", "FAIR": "📊"}


def _format_message(listing: dict, estimate: dict, profit: dict, deal_level: str) -> str:
    """Format a deal alert as Telegram MarkdownV2 message."""
    emoji = DEAL_EMOJI.get(deal_level, "📢")
    title = listing.get("title", "")[:60]
    platform = listing.get("platform", "").upper()
    price = listing.get("price", 0)
    est_value = estimate.get("estimated_value") or 0
    profit_eur = profit.get("profit_eur", 0)
    profit_pct = profit.get("profit_pct", 0)
    confidence = estimate.get("confidence", 0)
    category = listing.get("category", "")

    # Escape special chars for MarkdownV2
    def esc(s):
        chars = r"_*[]()~`>#+-=|{}.!"
        for c in chars:
            s = str(s).replace(c, f"\\{c}")
        return s

    lines = [
        f"{emoji} *{esc(deal_level)} DEAL \\- {esc(platform)}*",
        f"",
        f"*{esc(title)}*",
        f"",
        f"💰 Vraagprijs:   *€{esc(f'{price:.0f}')}*",
        f"📈 Marktwaarde:  *€{esc(f'{est_value:.0f}')}*",
        f"💵 Geschatte winst: *€{esc(f'{profit_eur:.0f}')} \\({esc(f'{profit_pct:.0%}')}\\)*",
        f"🎯 Betrouwbaarheid: {esc(f'{confidence:.0%}')}",
        f"🏷️ Categorie: {esc(category)}",
    ]

    return "\n".join(lines)


async def send_deal_alert(
    listing: dict,
    estimate: dict,
    profit: dict,
    deal_level: str,
) -> bool:
    """
    Send a deal alert via Telegram.

    Args:
        listing: Listing dict from database
        estimate: Estimate dict from price estimator
        profit: Profit dict from calculate_profit()
        deal_level: "EXCELLENT", "GOOD", or "FAIR"

    Returns:
        True if sent successfully
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID missing)")
        return False

    try:
        from aiogram import Bot
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        from aiogram.enums import ParseMode

        bot = Bot(token=TELEGRAM_BOT_TOKEN)

        text = _format_message(listing, estimate, profit, deal_level)

        # Inline keyboard with View Listing button
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="🔗 Bekijk advertentie",
                url=listing.get("url", "https://marktplaats.nl"),
            )
        ]])

        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=keyboard,
            disable_web_page_preview=False,
        )

        await bot.session.close()

        logger.info(f"Telegram alert sent: {listing.get('title', '')[:40]} — €{profit.get('profit_eur', 0):.0f}")
        return True

    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


async def send_system_message(message: str) -> bool:
    """Send a plain system notification (startup, errors, daily summary)."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    try:
        from aiogram import Bot

        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        await bot.session.close()
        return True
    except Exception as e:
        logger.error(f"Telegram system message failed: {e}")
        return False
