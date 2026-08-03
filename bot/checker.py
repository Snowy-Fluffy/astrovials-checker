import asyncio
import logging
from datetime import datetime, timezone

from aiogram import Bot

from bot import db
from bot.config import POLL_INTERVAL_SECONDS
from bot.notify import send_stock_notification
from bot.woocommerce import fetch_tracked_products

logger = logging.getLogger(__name__)


async def run_check_cycle(bot: Bot) -> None:
    snapshots = await fetch_tracked_products()
    if snapshots is None:
        return

    for slug, snapshot in snapshots.items():
        previous = await db.get_product_state(slug)

        await db.upsert_product_state(
            slug=snapshot.slug,
            name=snapshot.name,
            is_in_stock=snapshot.is_in_stock,
            price_eur=snapshot.price_eur,
            quantity=snapshot.quantity,
        )

        if previous is None:
            # First time we see this product — record baseline, don't notify.
            continue

        went_in_stock = (not previous["is_in_stock"]) and snapshot.is_in_stock
        if went_in_stock:
            logger.info("Product went in stock: %s", slug)
            await send_stock_notification(bot, snapshot)

    await db.set_meta("last_checked_at", datetime.now(timezone.utc).isoformat())


async def run_checker_loop(bot: Bot) -> None:
    while True:
        try:
            await run_check_cycle(bot)
        except Exception:
            logger.exception("Unhandled error in check cycle")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
