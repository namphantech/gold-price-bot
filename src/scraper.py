"""Scraper for the gold/silver price table on kimkhanhviethung.vn.

Strategy:
    1. Fetch the page with a plain ``requests`` GET and parse it with
       BeautifulSoup (fast, no browser dependency).
    2. If that yields no rows -- e.g. the site starts rendering the
       price table client-side with JavaScript -- transparently fall
       back to Playwright, render the page in headless Chromium, and
       parse the resulting HTML the same way.

Both paths share the same HTML parsing logic so behavior stays
consistent regardless of which fetch method was used.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

from config import REQUEST_TIMEOUT_SECONDS, SOURCE_URL, USER_AGENT

logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Raised when the gold price table cannot be retrieved or parsed."""


@dataclass(frozen=True)
class GoldPriceRow:
    """A single product row from the gold/silver price table."""

    category: str
    name: str
    buy_price: str
    sell_price: str
    converted_price: str


def _fetch_html_via_requests(url: str) -> str:
    """Fetch raw page HTML with a plain HTTP GET request.

    Raises:
        requests.RequestException: On network errors or non-2xx status.
    """
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    # The site does not always declare UTF-8 explicitly; let requests
    # sniff the real encoding so Vietnamese diacritics decode correctly.
    response.encoding = response.apparent_encoding or "utf-8"
    return response.text


def _fetch_html_via_playwright(url: str) -> str:
    """Fetch fully-rendered HTML using headless Chromium (Playwright).

    Used only as a fallback when the lightweight ``requests`` fetch does
    not yield any parseable price rows.

    Raises:
        ScraperError: If Playwright is unavailable or rendering fails.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise ScraperError(
            "Static parsing found no data and Playwright is not installed, "
            "so the JavaScript-rendering fallback is unavailable."
        ) from exc

    logger.info("Falling back to Playwright to render %s", url)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(user_agent=USER_AGENT)
                page.goto(
                    url,
                    timeout=REQUEST_TIMEOUT_SECONDS * 1000,
                    wait_until="networkidle",
                )
                html = page.content()
            finally:
                browser.close()
        return html
    except Exception as exc:  # noqa: BLE001 - normalize all Playwright failures
        raise ScraperError(f"Playwright rendering failed: {exc}") from exc


def _parse_gold_price_table(html: str) -> list[GoldPriceRow]:
    """Parse ``GoldPriceRow`` entries out of raw page HTML.

    The site's table markup is not fully well-formed (data rows are
    missing closing ``</tr>`` tags), so we parse with ``lxml``, which is
    lenient enough to still recover the correct row structure. Category
    section headers use ``<th>`` cells; product rows use ``<td>`` cells.
    """
    soup = BeautifulSoup(html, "lxml")
    table = soup.select_one("div.table_goldprice table")
    if table is None:
        return []

    rows: list[GoldPriceRow] = []
    current_category = "Khac"

    for tr in table.find_all("tr"):
        header_cells = tr.find_all("th")
        if header_cells:
            # A header row marks the start of a new category section
            # (e.g. "Vang 24K", "Vang cong ty", "BAC").
            current_category = header_cells[0].get_text(strip=True)
            continue

        data_cells = tr.find_all("td")
        if len(data_cells) < 3:
            continue

        name = data_cells[0].get_text(strip=True)
        if not name:
            continue

        buy_price = data_cells[1].get_text(strip=True)
        sell_price = data_cells[2].get_text(strip=True)
        converted_price = (
            data_cells[3].get_text(strip=True) if len(data_cells) > 3 else ""
        )

        rows.append(
            GoldPriceRow(
                category=current_category,
                name=name,
                buy_price=buy_price,
                sell_price=sell_price,
                converted_price=converted_price,
            )
        )

    return rows


def scrape_gold_prices(url: str = SOURCE_URL) -> list[GoldPriceRow]:
    """Scrape the current gold & silver price table from ``url``.

    Tries the cheap ``requests`` + BeautifulSoup path first, and only
    falls back to Playwright if no rows could be parsed from the static
    HTML (e.g. the page has become JavaScript-rendered).

    Raises:
        ScraperError: If the page cannot be fetched or no price rows can
            be parsed even after the Playwright fallback.
    """
    try:
        html = _fetch_html_via_requests(url)
    except requests.RequestException as exc:
        raise ScraperError(f"Failed to fetch page via requests: {exc}") from exc

    rows = _parse_gold_price_table(html)

    if not rows:
        logger.warning(
            "No rows found via static HTML parsing; attempting Playwright fallback."
        )
        html = _fetch_html_via_playwright(url)
        rows = _parse_gold_price_table(html)

    if not rows:
        raise ScraperError("Gold price table was empty after all scraping attempts.")

    logger.info("Scraped %d gold/silver price rows.", len(rows))
    return rows
