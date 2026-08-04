import time
from collections import defaultdict, deque
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.i18n import t

WINDOW_SECONDS = 60
MAX_EVENTS_IN_WINDOW = 10
MUTE_SECONDS = 30


class ThrottlingMiddleware(BaseMiddleware):
    """Mutes a user's commands/button presses for MUTE_SECONDS after they
    trigger more than MAX_EVENTS_IN_WINDOW events within WINDOW_SECONDS.
    Shared in-memory state across message and callback_query observers so
    flooding via either counts toward the same per-user limit."""

    def __init__(self) -> None:
        self._timestamps: dict[int, deque[float]] = defaultdict(deque)
        self._muted_until: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user is None:
            return await handler(event, data)

        user_id = user.id
        now = time.monotonic()

        muted_until = self._muted_until.get(user_id)
        if muted_until is not None and now < muted_until:
            if isinstance(event, CallbackQuery):
                await event.answer()
            return None

        timestamps = self._timestamps[user_id]
        timestamps.append(now)
        while timestamps and now - timestamps[0] > WINDOW_SECONDS:
            timestamps.popleft()

        if len(timestamps) > MAX_EVENTS_IN_WINDOW:
            self._muted_until[user_id] = now + MUTE_SECONDS
            timestamps.clear()
            text = t("throttled_notice", seconds=MUTE_SECONDS)
            if isinstance(event, Message):
                await event.answer(text)
            elif isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
            return None

        return await handler(event, data)
