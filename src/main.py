"""Entry point: scrape the daily gold price table and report it to Telegram.

Run directly (from the repo root):

    python src/main.py

Exits with status code 0 on success and 1 on any failure, so this can be
used directly as a GitHub Actions step that should fail the job when
something goes wrong.

For local runs, credentials can be placed in a ``.env`` file at the repo
root (see ``.env.example``); it is loaded automatically on startup. In
GitHub Actions, the real environment variables are injected by the
workflow from repository secrets, so no ``.env`` file is needed there.
"""

from __future__ import annotations

import logging
import sys

from dotenv import load_dotenv

from config import ConfigError, SOURCE_URL, load_telegram_config
from scraper import ScraperError, scrape_gold_prices
from telegram import TelegramError, build_report_message, send_telegram_message

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Set up basic console logging for the whole application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def run() -> int:
    """Run the scrape-then-notify pipeline once.

    Returns:
        A process exit code: ``0`` on success, ``1`` on any failure.
    """
    try:
        telegram_config = load_telegram_config()
        rows = scrape_gold_prices(SOURCE_URL)
        message = build_report_message(rows, SOURCE_URL)
        send_telegram_message(telegram_config, message)
    except ConfigError:
        logger.exception("Configuration error.")
        return 1
    except ScraperError:
        logger.exception("Scraping the gold price page failed.")
        return 1
    except TelegramError:
        logger.exception("Failed to deliver the Telegram report.")
        return 1
    except Exception:  # noqa: BLE001 - safety net so CI always sees a failure
        logger.exception("Unexpected error while running the gold price bot.")
        return 1

    logger.info("Gold price report sent successfully.")
    return 0


if __name__ == "__main__":
    load_dotenv()  # No-op if .env does not exist (e.g. in GitHub Actions).
    configure_logging()
    sys.exit(run())
