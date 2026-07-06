"""Report formatting and delivery via the Telegram Bot API."""

from __future__ import annotations

import logging
from datetime import datetime

import requests

from config import REQUEST_TIMEOUT_SECONDS, TELEGRAM_API_BASE, TelegramConfig
from scraper import GoldPriceRow

logger = logging.getLogger(__name__)

# Emoji picked by matching a keyword against the (lowercased) category
# name. Checked in order; falls back to a generic bar-chart emoji.
_CATEGORY_EMOJI: tuple[tuple[str, str], ...] = (
    ("bạc", "🥈"),
    ("vàng", "🥇"),
)


class TelegramError(Exception):
    """Raised when a message could not be delivered via the Telegram Bot API."""


def _emoji_for_category(category: str) -> str:
    """Pick a display emoji for a price-table category name."""
    lowered = category.lower()
    for keyword, emoji in _CATEGORY_EMOJI:
        if keyword in lowered:
            return emoji
    return "📊"


def build_report_message(rows: list[GoldPriceRow], source_url: str) -> str:
    """Build the formatted Telegram report text from scraped price rows.

    Rows are grouped under their category headings in the order they
    were scraped, e.g.::

        📅 Gold Price Report - 06/07/2026

        Vàng 24K
        🥇 Vàng 999.9 — Mua: 13.680.000đ | Bán: 13.880.000đ
        ...

        Source: https://kimkhanhviethung.vn/tra-cuu-gia-vang.html
    """
    today = datetime.now().strftime("%d/%m/%Y")
    lines: list[str] = [f"📅 <b>Gold Price Report</b> - {today}"]

    last_category: str | None = None
    for row in rows:
        if row.category != last_category:
            lines.append(f"\n<b>{row.category}</b>")
            last_category = row.category

        emoji = _emoji_for_category(row.category)
        lines.append(f"{emoji} {row.name} — Mua: {row.buy_price} | Bán: {row.sell_price}")

    lines.append(f"\nSource: {source_url}")
    return "\n".join(lines)


def send_telegram_message(config: TelegramConfig, text: str) -> None:
    """Send ``text`` to the configured Telegram chat via the Bot API.

    Raises:
        TelegramError: If the request fails or the API responds with an
            error.
    """
    url = f"{TELEGRAM_API_BASE}/bot{config.bot_token}/sendMessage"
    payload = {
        "chat_id": config.chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise TelegramError(f"Failed to reach Telegram API: {exc}") from exc

    payload_ok = False
    try:
        payload_ok = bool(response.json().get("ok", False))
    except ValueError:
        pass  # Non-JSON response; treated as a failure below.

    if response.status_code != 200 or not payload_ok:
        raise TelegramError(
            f"Telegram API returned an error (status={response.status_code}): "
            f"{response.text}"
        )

    logger.info("Telegram message sent successfully.")
