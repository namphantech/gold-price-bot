"""Configuration for the gold price bot.

Centralizes constants and environment-variable loading so the rest of
the codebase never touches ``os.environ`` directly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# --- Scraper constants ------------------------------------------------

SOURCE_URL: str = "https://kimkhanhviethung.vn/tra-cuu-gia-vang.html"
REQUEST_TIMEOUT_SECONDS: int = 15
USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# --- Telegram constants -------------------------------------------------

TELEGRAM_API_BASE: str = "https://api.telegram.org"


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class TelegramConfig:
    """Telegram credentials required to deliver the report."""

    bot_token: str
    chat_id: str


def load_telegram_config() -> TelegramConfig:
    """Load and validate Telegram credentials from environment variables.

    Raises:
        ConfigError: If ``TELEGRAM_BOT_TOKEN`` or ``TELEGRAM_CHAT_ID`` is
            missing or empty.
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    missing = [
        name
        for name, value in (
            ("TELEGRAM_BOT_TOKEN", bot_token),
            ("TELEGRAM_CHAT_ID", chat_id),
        )
        if not value
    ]
    if missing:
        raise ConfigError(
            "Missing required environment variable(s): " + ", ".join(missing)
        )

    return TelegramConfig(bot_token=bot_token, chat_id=chat_id)
