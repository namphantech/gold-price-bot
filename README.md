# gold-bot

Scrapes the daily gold & silver price table from
[kimkhanhviethung.vn](https://kimkhanhviethung.vn/tra-cuu-gia-vang.html) and
sends a formatted report to a Telegram chat, once a day via GitHub Actions.

> **Note on the source site:** kimkhanhviethung.vn is a local Vietnamese
> jewelry shop, not the national SJC brand — its table lists categories like
> "Vàng 24K", "Vàng 417 (KKVH)", "Vàng công ty" and "BẠC" (silver) rather than
> "SJC". The bot reports whatever rows are present on the page rather than
> hardcoding specific product names, so it keeps working if the shop adds or
> renames products.

## How it works

1. `src/scraper.py` fetches the page with `requests` and parses the price
   table with BeautifulSoup. If no rows can be parsed (e.g. the site starts
   rendering the table with JavaScript), it automatically retries by
   rendering the page with headless Chromium via Playwright.
2. `src/telegram.py` formats the scraped rows into a readable message and
   sends it through the Telegram Bot API.
3. `src/main.py` wires the two together, logs progress/errors, and exits
   with status `1` on any failure (network error, empty table, missing
   config, Telegram API error) so a failed GitHub Actions run is clearly
   flagged.

## Project structure

```
.
├── .github/
│   └── workflows/
│       └── gold-price.yml   # Daily schedule + manual trigger
├── src/
│   ├── config.py            # Constants + environment variable loading
│   ├── scraper.py           # requests/BeautifulSoup scraping + Playwright fallback
│   ├── telegram.py          # Report formatting + Telegram Bot API delivery
│   └── main.py              # Entry point / orchestration
├── requirements.txt
├── .gitignore
└── README.md
```

## Local setup

Requires Python 3.12.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Only needed if the Playwright fallback ever triggers locally:
playwright install --with-deps chromium
```

Set the required environment variables and run the script:

```bash
export TELEGRAM_BOT_TOKEN="123456789:AAExampleTokenValue"
export TELEGRAM_CHAT_ID="123456789"
python src/main.py
```

On success it logs `Gold price report sent successfully.` and exits `0`. On
failure it logs the error with a traceback and exits `1`.

## Getting your Telegram credentials

1. **Create a bot** — message [@BotFather](https://t.me/BotFather) on
   Telegram, send `/newbot`, and follow the prompts. It replies with a bot
   token that looks like `123456789:AAExampleTokenValue` — this is your
   `TELEGRAM_BOT_TOKEN`.
2. **Get your chat ID** — start a chat with your new bot (or add it to a
   group) and send it any message, then open:
   `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   Find `"chat":{"id": ...}` in the JSON response — that number is your
   `TELEGRAM_CHAT_ID`. (For groups, this is usually a negative number.)

## Configuring GitHub Secrets

In your GitHub repository, go to **Settings → Secrets and variables →
Actions → New repository secret** and add:

| Secret name           | Value                                  |
|------------------------|-----------------------------------------|
| `TELEGRAM_BOT_TOKEN`   | The token from BotFather                |
| `TELEGRAM_CHAT_ID`     | The chat ID you want the report sent to |

No other configuration is needed — the workflow reads both secrets
automatically.

## GitHub Actions workflow

`.github/workflows/gold-price.yml`:

- Runs daily at **08:00 Asia/Ho_Chi_Minh** (`01:00 UTC`, cron `0 1 * * *`).
- Can also be triggered manually from the **Actions** tab via
  `workflow_dispatch`.
- Installs dependencies from `requirements.txt` and the Playwright Chromium
  browser (used only if the JavaScript-rendering fallback is needed).
- Runs `python src/main.py` with the two secrets injected as environment
  variables.
- Fails the job (non-zero exit) if scraping or sending the report fails, so
  you'll see a red ❌ in the Actions tab instead of a silent skip.

## Example report

```
📅 Gold Price Report - 06/07/2026

Vàng 24K
🥇 Vàng 999.9 — Mua: 13.680.000đ | Bán: 13.880.000đ
🥇 Vàng Nhẫn Khâu 98 — Mua: 13.340.000đ | Bán: 13.500.000đ
...

BẠC
🥈 Bạc Thỏi Phát Lộc (1 kilo) — Mua: 66.400.000đ | Bán: 68.930.000đ
...

Source: https://kimkhanhviethung.vn/tra-cuu-gia-vang.html
```
