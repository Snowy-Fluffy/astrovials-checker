from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from bot import db
from bot.currency import get_eur_rub_rate
from bot.i18n import t
from bot.products import PRODUCTS, PRODUCTS_BY_SLUG

router = Router()


async def _build_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    selected = await db.get_subscriptions(chat_id)
    rows = []
    for product in PRODUCTS:
        mark = "✅" if product.slug in selected else "⬜"
        rows.append(
            [InlineKeyboardButton(text=f"{mark} {product.name}", callback_data=f"toggle:{product.slug}")]
        )
    rows.append([InlineKeyboardButton(text=t("btn_done"), callback_data="done")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await db.upsert_user(message.chat.id)
    keyboard = await _build_keyboard(message.chat.id)
    await message.answer(t("start_prompt"), reply_markup=keyboard)


@router.callback_query(lambda c: c.data and c.data.startswith("toggle:"))
async def cb_toggle(callback: CallbackQuery) -> None:
    slug = callback.data.split(":", 1)[1]
    if slug not in PRODUCTS_BY_SLUG:
        await callback.answer()
        return
    await db.toggle_subscription(callback.message.chat.id, slug)
    keyboard = await _build_keyboard(callback.message.chat.id)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()


@router.callback_query(lambda c: c.data == "done")
async def cb_done(callback: CallbackQuery) -> None:
    selected = await db.get_subscriptions(callback.message.chat.id)
    if selected:
        names = [p.name for p in PRODUCTS if p.slug in selected]
        items = "\n".join(f"• {n}" for n in names)
        text = t("watchlist_summary", items=items)
    else:
        text = t("watchlist_empty")
    await callback.message.edit_text(text)
    await callback.answer(t("saved"))


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    last_checked_at = await db.get_meta("last_checked_at")
    states = await db.get_all_product_states()
    rate = await get_eur_rub_rate()

    if last_checked_at:
        checked_dt = datetime.fromisoformat(last_checked_at)
        header = t("status_last_check", time=checked_dt.strftime("%Y-%m-%d %H:%M:%S"))
    else:
        header = t("status_never_checked")

    lines = [header, ""]
    for product in PRODUCTS:
        state = states.get(product.slug)
        if state is None:
            lines.append(t("status_no_data", name=product.name))
            continue

        if state["is_in_stock"]:
            line = f"✅ {product.name}"
        else:
            line = f"❌ {t('status_out_of_stock')}: {product.name}"
        if state["price_eur"] is not None:
            price = state["price_eur"]
            rub_part = t("notify_rub", rub=f"{price * rate:,.0f}".replace(",", " ")) if rate else ""
            line += f" — {price:.2f} €{rub_part}"
        if state["is_in_stock"] and state["quantity"] is not None:
            line += f", {state['quantity']} {t('unit_pcs')}"
        lines.append(line)

    await message.answer("\n".join(lines))
