# astrovials-checker

A Telegram bot that checks stock status for 5 products on
https://astrovials.com every minute (via the site's public WooCommerce Store
API) and notifies subscribed users when something comes back in stock — with
the price in € and the converted price in ₽ (Bank of Russia rate).

## Features

- `/start` — pick (or change) which products to track via inline buttons.
- `/status` — time of the last check (UTC) and a summary for all 5 products.
- Automatic check every minute (configurable), notifying only on the
  "out of stock → in stock" transition.
- Bilingual: bot messages are available in Russian and English, selected via
  the `LOCALE` setting in `.env`.
- Flood protection: broadcasts to subscribers are throttled and retry
  automatically on Telegram rate limits; a user sending more than 10
  commands/button presses within 60 seconds is muted for 30 seconds.
- `/broadcast <text>` — admin-only (see `ADMIN_USER_IDS`), sends a custom
  message to everyone who has ever run `/start`.

Limitation: the site doesn't always expose the exact quantity in stock
through the public API. The bot tries to extract a number from the stock
status text; if it's not there, the notification is sent without a quantity
line.

## Running it

1. Create a bot with [@BotFather](https://t.me/BotFather): `/newbot`, follow
   the prompts, copy the token you're given.
2. Copy `.env.example` to `.env` and fill in the token:
   ```
   cp .env.example .env
   ```
   Open `.env` and set `TELEGRAM_BOT_TOKEN=...`.
3. Build and start the container:
   ```
   docker compose up -d --build
   ```
4. Check the logs:
   ```
   docker compose logs -f
   ```
   You should see the bot starting up and the first check cycle completing
   without errors.
5. Message your bot `/start` on Telegram.

## Data

The SQLite database lives at `./data/bot.db` (mounted as a volume), so it
survives container rebuilds and restarts. It stores users, their
subscriptions, the last known state of each product, and the timestamp of
the last successful check.

## Settings (.env)

| Variable | Default | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | — | Bot token from @BotFather (required) |
| `POLL_INTERVAL_SECONDS` | 60 | How often to check the site |
| `CURRENCY_REFRESH_SECONDS` | 3600 | How often to refresh the EUR→RUB rate |
| `LOCALE` | ru | Bot language: `ru` or `en` |
| `ADMIN_USER_IDS` | — | Comma-separated Telegram user IDs allowed to use `/broadcast` (disabled if empty) |

## Stopping

```
docker compose down
```

Data in `./data/` is preserved.

## License

GPLv3 — see [LICENSE](LICENSE).
