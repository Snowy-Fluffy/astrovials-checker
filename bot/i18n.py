from bot.config import LOCALE

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "ru": {
        "start_prompt": (
            "Выберите препараты, о появлении которых в наличии хотите узнавать.\n"
            "Нажмите на нужные, затем «Готово». Список можно поменять в любой момент "
            "командой /start.\n\n"
            "Бот автоматически пришлет вам уведомление, как только препарат будет в наличии"
        ),
        "btn_done": "✅ Готово",
        "watchlist_summary": "Буду уведомлять о появлении в наличии:\n{items}",
        "watchlist_empty": "Список отслеживания пуст. Вызовите /start, чтобы выбрать препараты.",
        "saved": "Сохранено",
        "status_last_check": "Последняя проверка: {time} UTC",
        "status_never_checked": "Проверка ещё не выполнялась.",
        "status_no_data": "❔ {name} — нет данных",
        "unit_pcs": "шт.",
        "notify_title": "🟢 Появилось в наличии!",
        "notify_price": "Цена: {price} €{rub_part}",
        "notify_rub": " (~{rub} ₽ по курсу ЦБ)",
        "notify_qty": "В наличии: {qty} {unit}",
        "notify_link": "Ссылка: {url}",
        "status_out_of_stock": "нет в наличии",
        "cmd_start_description": "Выбрать препараты для отслеживания",
        "cmd_status_description": "Статус проверки и наличие препаратов",
    },
    "en": {
        "start_prompt": (
            "Choose the products you'd like to be notified about when they're back in "
            "stock.\nTap the ones you want, then \"Done\". You can change the list "
            "anytime with /start.\n\n"
            "The bot will automatically send you a notification as soon as the medication is in stock"
        ),
        "btn_done": "✅ Done",
        "watchlist_summary": "You'll be notified when these are back in stock:\n{items}",
        "watchlist_empty": "Your watch list is empty. Use /start to pick products.",
        "saved": "Saved",
        "status_last_check": "Last check: {time} UTC",
        "status_never_checked": "No check has been performed yet.",
        "status_no_data": "❔ {name} — no data",
        "unit_pcs": "pcs",
        "notify_title": "🟢 Back in stock!",
        "notify_price": "Price: {price} €{rub_part}",
        "notify_rub": " (~{rub} ₽ at CBR rate)",
        "notify_qty": "In stock: {qty} {unit}",
        "notify_link": "Link: {url}",
        "status_out_of_stock": "not in stock",
        "cmd_start_description": "Choose products to track",
        "cmd_status_description": "Check status and stock summary",
    },
}


def t(key: str, **kwargs) -> str:
    template = _TRANSLATIONS[LOCALE][key]
    return template.format(**kwargs) if kwargs else template
