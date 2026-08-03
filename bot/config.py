import logging
import os

logger = logging.getLogger(__name__)

MIN_POLL_INTERVAL_SECONDS = 5


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    value = os.environ.get(name)
    if not value:
        return default
    try:
        parsed = int(value)
    except ValueError:
        logger.warning("Invalid value for %s=%r, falling back to %d", name, value, default)
        return default
    if parsed < minimum:
        logger.warning(
            "%s=%d is below the minimum (%d), clamping to %d", name, parsed, minimum, minimum
        )
        return minimum
    return parsed


SUPPORTED_LOCALES = ("ru", "en")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
POLL_INTERVAL_SECONDS = _env_int("POLL_INTERVAL_SECONDS", 60, minimum=MIN_POLL_INTERVAL_SECONDS)
CURRENCY_REFRESH_SECONDS = _env_int("CURRENCY_REFRESH_SECONDS", 3600, minimum=MIN_POLL_INTERVAL_SECONDS)
DB_PATH = os.environ.get("DB_PATH", "data/bot.db")

_locale = os.environ.get("LOCALE", "ru").strip().lower()
LOCALE = _locale if _locale in SUPPORTED_LOCALES else "ru"

WOOCOMMERCE_API_URL = "https://astrovials.com/wp-json/wc/store/v1/products"
CURRENCY_API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"

HTTP_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
HTTP_TIMEOUT_SECONDS = 15
