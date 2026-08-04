import logging
import re

import aiohttp

from bot.config import HTTP_TIMEOUT_SECONDS, HTTP_USER_AGENT, WOOCOMMERCE_API_URL
from bot.products import PRODUCTS_BY_SLUG

logger = logging.getLogger(__name__)

_QUANTITY_PATTERNS = [
    re.compile(r"only\s+(\d+)\s+left\s+in\s+stock", re.IGNORECASE),
    re.compile(r"(\d+)\s+in\s+stock", re.IGNORECASE),
    re.compile(r"(\d+)\s+left", re.IGNORECASE),
]


class ProductSnapshot:
    def __init__(self, slug: str, name: str, is_in_stock: bool, price_eur: float | None, quantity: int | None):
        self.slug = slug
        self.name = name
        self.is_in_stock = is_in_stock
        self.price_eur = price_eur
        self.quantity = quantity


def _extract_quantity(item: dict) -> int | None:
    low_stock_remaining = item.get("low_stock_remaining")
    if isinstance(low_stock_remaining, int):
        return low_stock_remaining

    stock_text = (item.get("stock_availability") or {}).get("text")
    if not stock_text:
        return None
    for pattern in _QUANTITY_PATTERNS:
        match = pattern.search(stock_text)
        if match:
            return int(match.group(1))
    return None


def _extract_price_eur(prices: dict) -> float | None:
    raw_price = prices.get("price")
    minor_unit = prices.get("currency_minor_unit")
    if raw_price is None or minor_unit is None:
        return None
    try:
        return int(raw_price) / (10 ** int(minor_unit))
    except (TypeError, ValueError):
        return None


async def fetch_tracked_products() -> dict[str, ProductSnapshot] | None:
    """Fetches all products from the Store API and returns a snapshot for each
    tracked slug. Returns None on network/parse failure so the caller can skip
    the cycle without corrupting last-known state."""
    headers = {"User-Agent": HTTP_USER_AGENT, "Accept": "application/json"}
    timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SECONDS)
    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(WOOCOMMERCE_API_URL, params={"per_page": 100}) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)
    except (aiohttp.ClientError, TimeoutError) as exc:
        logger.warning("Failed to fetch WooCommerce store API: %s", exc)
        return None
    except Exception:
        logger.exception("Unexpected error fetching WooCommerce store API")
        return None

    if not isinstance(data, list):
        logger.warning("Unexpected WooCommerce store API response shape: %r", type(data))
        return None

    try:
        snapshots: dict[str, ProductSnapshot] = {}
        for item in data:
            slug = item.get("slug")
            if slug not in PRODUCTS_BY_SLUG:
                continue
            prices = item.get("prices") or {}
            snapshots[slug] = ProductSnapshot(
                slug=slug,
                name=PRODUCTS_BY_SLUG[slug].name,
                is_in_stock=bool(item.get("is_in_stock")),
                price_eur=_extract_price_eur(prices),
                quantity=_extract_quantity(item),
            )
    except (AttributeError, TypeError):
        logger.exception("Failed to parse WooCommerce store API response")
        return None

    missing = set(PRODUCTS_BY_SLUG) - set(snapshots)
    if missing:
        logger.warning("Tracked products missing from API response: %s", missing)

    return snapshots
