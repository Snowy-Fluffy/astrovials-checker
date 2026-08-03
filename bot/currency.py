import logging
import time

import aiohttp

from bot.config import CURRENCY_API_URL, CURRENCY_REFRESH_SECONDS, HTTP_TIMEOUT_SECONDS, HTTP_USER_AGENT

logger = logging.getLogger(__name__)

_cached_rate: float | None = None
_cached_at: float = 0.0


async def _fetch_rate() -> float | None:
    headers = {"User-Agent": HTTP_USER_AGENT, "Accept": "application/json"}
    timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SECONDS)
    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(CURRENCY_API_URL) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)
                return float(data["Valute"]["EUR"]["Value"])
    except Exception as exc:
        logger.warning("Failed to fetch EUR/RUB rate: %s", exc)
        return None


async def get_eur_rub_rate() -> float | None:
    """Returns the cached EUR->RUB rate, refreshing it if stale. Falls back to
    the last known rate (even if stale) if a refresh fails, so notifications
    never get blocked just because the currency API is down."""
    global _cached_rate, _cached_at

    is_stale = (time.monotonic() - _cached_at) > CURRENCY_REFRESH_SECONDS
    if _cached_rate is None or is_stale:
        fresh_rate = await _fetch_rate()
        if fresh_rate is not None:
            _cached_rate = fresh_rate
            _cached_at = time.monotonic()
        elif _cached_rate is None:
            return None

    return _cached_rate
