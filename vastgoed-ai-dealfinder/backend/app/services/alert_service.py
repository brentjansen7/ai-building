import aiohttp
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
import structlog

from app.config import settings

logger = structlog.get_logger()


class AlertService:
    """Verstuur deal alerts via Telegram, Discord en Email."""

    def __init__(self):
        self.telegram_token = settings.telegram_token
        self.telegram_chat_id = settings.telegram_chat_id
        self.discord_webhook = settings.discord_webhook_url
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_pass = settings.smtp_pass
        self.alert_email = settings.alert_email

    def should_alert(self, deal_score: int, deal_grade: str, roi_pct: float, profit: int) -> bool:
        """Bepaal of we een alert moeten sturen."""
        return (
            deal_score >= settings.min_deal_score
            and deal_grade in settings.alert_grades_list
            and roi_pct >= settings.min_roi_percentage
            and profit >= settings.min_profit
        )

    async def send_all(self, listing: Dict, analysis: Dict) -> Dict[str, bool]:
        """Stuur alert via alle kanalen tegelijk."""
        results = {}

        tasks = []
        if self.telegram_token and self.telegram_chat_id:
            tasks.append(("telegram", self.send_telegram(listing, analysis)))
        if self.discord_webhook:
            tasks.append(("discord", self.send_discord(listing, analysis)))
        if self.alert_email and self.smtp_user:
            tasks.append(("email", self.send_email(listing, analysis)))

        for name, coro in tasks:
            try:
                results[name] = await coro
            except Exception as e:
                logger.error("Alert fout", channel=name, error=str(e))
                results[name] = False

        return results

    async def send_telegram(self, listing: Dict, analysis: Dict) -> bool:
        """Stuur Telegram melding."""
        try:
            text = self._build_telegram_message(listing, analysis)
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"

            async with aiohttp.ClientSession() as session:
                payload = {
                    "chat_id": self.telegram_chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False,
                }
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json()
                    if data.get("ok"):
                        logger.info("Telegram alert verstuurd", listing_id=listing.get("id"))
                        return True
                    else:
                        logger.warning("Telegram fout", response=data)
                        return False

        except Exception as e:
            logger.error("Telegram alert fout", error=str(e))
            return False

    async def send_discord(self, listing: Dict, analysis: Dict) -> bool:
        """Stuur Discord webhook melding."""
        try:
            grade = analysis.get("deal_grade", "?")
            score = analysis.get("deal_score", 0)
            profit = analysis.get("potential_profit", 0)
            roi = analysis.get("roi_percentage", 0)

            color = {
                "A": 0x22C55E,   # Groen
                "B": 0x3B82F6,   # Blauw
                "C": 0xF59E0B,   # Geel
                "D": 0xEF4444,   # Rood
                "F": 0x6B7280,   # Grijs
            }.get(grade, 0x6B7280)

            embed = {
                "title": f"🏠 Nieuwe Vastgoeddeal | Grade {grade} ({score}/100)",
                "description": analysis.get("verdict", ""),
                "color": color,
                "url": listing.get("url", ""),
                "fields": [
                    {"name": "📍 Locatie", "value": f"{listing.get('address', '')}, {listing.get('city', '')}", "inline": True},
                    {"name": "💰 Vraagprijs", "value": f"€{listing.get('price_ask', 0):,}", "inline": True},
                    {"name": "📋 WOZ Waarde", "value": f"€{listing.get('woz_value', 0):,}" if listing.get('woz_value') else "Onbekend", "inline": True},
                    {"name": "🔨 Renovatiekosten", "value": f"€{analysis.get('reno_cost_mid', 0):,}", "inline": True},
                    {"name": "📈 Waarde na reno", "value": f"€{analysis.get('estimated_value_after_reno', 0):,}", "inline": True},
                    {"name": "💵 Potentiële winst", "value": f"**€{profit:,}**", "inline": True},
                    {"name": "📊 ROI", "value": f"{roi:.1f}%", "inline": True},
                    {"name": "🏚️ Kluswoning", "value": f"{'Ja' if listing.get('is_klus_likely') else 'Nee'} ({listing.get('klus_confidence', 0):.0%})", "inline": True},
                ],
                "footer": {"text": "Vastgoed AI Dealfinder"},
            }

            async with aiohttp.ClientSession() as session:
                payload = {"embeds": [embed]}
                async with session.post(
                    self.discord_webhook,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status in (200, 204):
                        logger.info("Discord alert verstuurd")
                        return True
                    else:
                        logger.warning("Discord fout", status=resp.status)
                        return False

        except Exception as e:
            logger.error("Discord alert fout", error=str(e))
            return False

    async def send_email(self, listing: Dict, analysis: Dict) -> bool:
        """Stuur email melding."""
        try:
            msg = MIMEMultipart("alternative")
            grade = analysis.get("deal_grade", "?")
            city = listing.get("city", "")

            msg["Subject"] = f"[Deal {grade}] Nieuwe kluswoning in {city} - €{analysis.get('potential_profit', 0):,} winst"
            msg["From"] = self.smtp_user
            msg["To"] = self.alert_email

            html_body = self._build_email_html(listing, analysis)
            msg.attach(MIMEText(html_body, "html"))

            # Asynchroon SMTP (run in thread)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_smtp, msg)
            logger.info("Email alert verstuurd", to=self.alert_email)
            return True

        except Exception as e:
            logger.error("Email alert fout", error=str(e))
            return False

    def _send_smtp(self, msg: MIMEMultipart):
        """Stuur via SMTP (blocking, gebruik in thread)."""
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_user, self.smtp_pass)
            server.send_message(msg)

    def _build_telegram_message(self, listing: Dict, analysis: Dict) -> str:
        """Bouw Telegram HTML bericht."""
        grade = analysis.get("deal_grade", "?")
        score = analysis.get("deal_score", 0)
        profit = analysis.get("potential_profit", 0)
        roi = analysis.get("roi_percentage", 0.0)
        reno = analysis.get("reno_cost_mid", 0)
        value = analysis.get("estimated_value_after_reno", 0)
        address = listing.get("address", "")
        city = listing.get("city", "")
        price = listing.get("price_ask", 0)
        woz = listing.get("woz_value", 0)
        url = listing.get("url", "")

        grade_emoji = {"A": "🟢", "B": "🔵", "C": "🟡", "D": "🟠", "F": "🔴"}.get(grade, "⚪")

        lines = [
            f"{grade_emoji} <b>Nieuwe Vastgoeddeal — Grade {grade} ({score}/100)</b>",
            "",
            f"📍 <b>{address}, {city}</b>",
            f"🔗 <a href='{url}'>Bekijk advertentie</a>",
            "",
            f"💰 Vraagprijs: <b>€{price:,}</b>",
        ]

        if woz:
            diff = woz - price
            sign = "+" if diff > 0 else ""
            lines.append(f"📋 WOZ waarde: <b>€{woz:,}</b> ({sign}€{diff:,})")

        lines += [
            f"🔨 Renovatiekosten: <b>€{reno:,}</b>",
            f"🏠 Waarde na renovatie: <b>€{value:,}</b>",
            "",
            f"💵 Potentiële winst: <b>€{profit:,}</b>",
            f"📈 ROI: <b>{roi:.1f}%</b>",
            "",
            f"🎯 {analysis.get('verdict', '')}",
        ]

        return "\n".join(lines)

    def _build_email_html(self, listing: Dict, analysis: Dict) -> str:
        """Bouw HTML email body."""
        grade = analysis.get("deal_grade", "?")
        score = analysis.get("deal_score", 0)
        profit = analysis.get("potential_profit", 0)
        roi = analysis.get("roi_percentage", 0.0)
        reno = analysis.get("reno_cost_mid", 0)
        value = analysis.get("estimated_value_after_reno", 0)
        address = listing.get("address", "")
        city = listing.get("city", "")
        price = listing.get("price_ask", 0)
        woz = listing.get("woz_value", 0)
        url = listing.get("url", "#")

        grade_color = {"A": "#22C55E", "B": "#3B82F6", "C": "#F59E0B", "D": "#EF4444", "F": "#6B7280"}.get(grade, "#6B7280")

        return f"""
<!DOCTYPE html>
<html lang="nl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width"></head>
<body style="margin:0;padding:20px;font-family:Arial,sans-serif;background:#f3f4f6;">
<div style="max-width:600px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.1);">

  <div style="background:{grade_color};padding:24px;color:white;text-align:center;">
    <div style="font-size:48px;font-weight:bold;">{grade}</div>
    <div style="font-size:20px;margin-top:4px;">Deal Score: {score}/100</div>
    <div style="font-size:14px;opacity:0.85;margin-top:8px;">{city}</div>
  </div>

  <div style="padding:24px;">
    <h2 style="margin:0 0 4px;font-size:18px;">{address}</h2>
    <a href="{url}" style="color:#3B82F6;font-size:14px;">Bekijk advertentie →</a>

    <table style="width:100%;margin-top:20px;border-collapse:collapse;">
      <tr style="background:#f9fafb;">
        <td style="padding:12px;font-weight:bold;">Vraagprijs</td>
        <td style="padding:12px;text-align:right;font-size:18px;font-weight:bold;">€{price:,}</td>
      </tr>
      <tr>
        <td style="padding:12px;">WOZ Waarde</td>
        <td style="padding:12px;text-align:right;color:#22C55E;font-weight:bold;">€{woz:,}</td>
      </tr>
      <tr style="background:#f9fafb;">
        <td style="padding:12px;">Renovatiekosten</td>
        <td style="padding:12px;text-align:right;">€{reno:,}</td>
      </tr>
      <tr>
        <td style="padding:12px;">Waarde na renovatie</td>
        <td style="padding:12px;text-align:right;font-weight:bold;">€{value:,}</td>
      </tr>
      <tr style="background:#f0fdf4;">
        <td style="padding:12px;font-weight:bold;color:#15803D;">Potentiële winst</td>
        <td style="padding:12px;text-align:right;font-size:20px;font-weight:bold;color:#15803D;">€{profit:,}</td>
      </tr>
      <tr>
        <td style="padding:12px;">ROI</td>
        <td style="padding:12px;text-align:right;font-weight:bold;">{roi:.1f}%</td>
      </tr>
    </table>

    <div style="margin-top:20px;padding:16px;background:#EFF6FF;border-radius:8px;font-size:14px;">
      <b>Analyse:</b> {analysis.get('verdict', '')}
    </div>

    <a href="{url}" style="display:block;margin-top:20px;padding:14px;background:{grade_color};color:white;text-align:center;text-decoration:none;border-radius:8px;font-weight:bold;font-size:16px;">
      Bekijk Woning →
    </a>
  </div>

  <div style="padding:16px;text-align:center;font-size:12px;color:#9CA3AF;border-top:1px solid #F3F4F6;">
    Vastgoed AI Dealfinder
  </div>
</div>
</body>
</html>"""
