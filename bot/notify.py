import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from bot import db
from bot.currency import get_eur_rub_rate
from bot.i18n import t
from bot.products import PRODUCTS_BY_SLUG
from bot.woocommerce import ProductSnapshot

logger = logging.getLogger(__name__)


def _format_rub(price_eur: float, rate: float | None) -> str:
    if rate is None:
        return ""
    rub = price_eur * rate
    return t("notify_rub", rub=f"{rub:,.0f}".replace(",", " "))


async def _build_message(snapshot: ProductSnapshot) -> str:
    product = PRODUCTS_BY_SLUG[snapshot.slug]
    rate = await get_eur_rub_rate()

    lines = [t("notify_title"), "", product.name]

    if snapshot.price_eur is not None:
        rub_part = _format_rub(snapshot.price_eur, rate)
        lines.append(t("notify_price", price=f"{snapshot.price_eur:.2f}", rub_part=rub_part))

    if snapshot.quantity is not None:
        lines.append(t("notify_qty", qty=snapshot.quantity, unit=t("unit_pcs")))

    lines.append(t("notify_link", url=product.url))
    return "\n".join(lines)


async def send_stock_notification(bot: Bot, snapshot: ProductSnapshot) -> None:
    message = await _build_message(snapshot)
    chat_ids = await db.get_subscribers(snapshot.slug)

    for chat_id in chat_ids:
        try:
            await bot.send_message(chat_id, message)
        except TelegramAPIError as exc:
            logger.warning("Failed to notify chat_id=%s: %s", chat_id, exc)
