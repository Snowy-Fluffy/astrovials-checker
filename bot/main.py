import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from bot import db
from bot.checker import run_checker_loop
from bot.config import TELEGRAM_BOT_TOKEN
from bot.handlers import router
from bot.i18n import t
from bot.throttling import ThrottlingMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set (check your .env)")

    await db.init_db()

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dispatcher = Dispatcher()
    dispatcher.include_router(router)

    throttling = ThrottlingMiddleware()
    dispatcher.message.outer_middleware(throttling)
    dispatcher.callback_query.outer_middleware(throttling)

    await bot.set_my_commands([
        BotCommand(command="start", description=t("cmd_start_description")),
        BotCommand(command="status", description=t("cmd_status_description")),
    ])

    checker_task = asyncio.create_task(run_checker_loop(bot))
    logger.info("Bot starting, poll interval check task launched")

    try:
        await dispatcher.start_polling(bot)
    finally:
        checker_task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
