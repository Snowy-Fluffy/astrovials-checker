import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError, TelegramRetryAfter

from bot import db
from bot.currency import get_eur_rub_rate
from bot.i18n import t
from bot.products import PRODUCTS_BY_SLUG
from bot.woocommerce import ProductSnapshot

logger = logging.getLogger(__name__)

# ~20 messages/sec, comfortably under Telegram's global ~30 msg/sec bot limit.
BROADCAST_DELAY_SECONDS = 0.05


def _format_rub(price_eur: float, rate: float | None) -> str:
    if rate is None:
        return ""
    rub = price_eur * rate
    return t("notify_rub", rub=f"{rub:,.0f}".replace(",", " "))


async def _build_message(snapshot: ProductSnapshot, title_key: str) -> str:
    product = PRODUCTS_BY_SLUG[snapshot.slug]
    rate = await get_eur_rub_rate()

    lines = [t(title_key), "", product.name]

    if snapshot.price_eur is not None:
        rub_part = _format_rub(snapshot.price_eur, rate)
        lines.append(t("notify_price", price=f"{snapshot.price_eur:.2f}", rub_part=rub_part))

    if snapshot.quantity is not None:
        lines.append(t("notify_qty", qty=snapshot.quantity, unit=t("unit_pcs")))

    lines.append(t("notify_link", url=product.url))
    return "\n".join(lines)


async def _send_to_chat(bot: Bot, chat_id: int, message: str, parse_mode: str | None = None) -> bool:
    try:
        await bot.send_message(chat_id, message, parse_mode=parse_mode)
        return True
    except TelegramRetryAfter as exc:
        logger.warning("Rate limited by Telegram, sleeping %.1fs before retrying chat_id=%s", exc.retry_after, chat_id)
        await asyncio.sleep(exc.retry_after)
        try:
            await bot.send_message(chat_id, message, parse_mode=parse_mode)
            return True
        except TelegramForbiddenError:
            logger.info("chat_id=%s blocked the bot, removing them", chat_id)
            await db.delete_user(chat_id)
            return False
        except TelegramAPIError as exc2:
            logger.warning("Failed to send to chat_id=%s after retry: %s", chat_id, exc2)
            return False
    except TelegramForbiddenError:
        logger.info("chat_id=%s blocked the bot, removing them", chat_id)
        await db.delete_user(chat_id)
        return False
    except TelegramAPIError as exc:
        logger.warning("Failed to send to chat_id=%s: %s", chat_id, exc)
        return False


async def broadcast(
    bot: Bot, chat_ids: list[int], message: str, parse_mode: str | None = None
) -> tuple[int, int]:
    """Sends message to every chat_id with a small delay between sends and
    automatic retry-on-429 handling. Returns (sent, failed) counts."""
    sent = 0
    for chat_id in chat_ids:
        if await _send_to_chat(bot, chat_id, message, parse_mode):
            sent += 1
        await asyncio.sleep(BROADCAST_DELAY_SECONDS)
    return sent, len(chat_ids) - sent


async def send_stock_notification(bot: Bot, snapshot: ProductSnapshot) -> None:
    message = await _build_message(snapshot, "notify_title")
    chat_ids = await db.get_subscribers(snapshot.slug)
    await broadcast(bot, chat_ids, message)


async def send_already_in_stock_notification(bot: Bot, chat_id: int, snapshot: ProductSnapshot) -> None:
    message = await _build_message(snapshot, "notify_already_title")
    await _send_to_chat(bot, chat_id, message)
