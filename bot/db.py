import os
from datetime import datetime, timezone

import aiosqlite

from bot.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    chat_id INTEGER PRIMARY KEY,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subscriptions (
    chat_id INTEGER NOT NULL,
    product_slug TEXT NOT NULL,
    PRIMARY KEY (chat_id, product_slug)
);

CREATE TABLE IF NOT EXISTS product_state (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    is_in_stock INTEGER NOT NULL,
    price_eur REAL,
    quantity INTEGER,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


async def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def upsert_user(chat_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO users (chat_id, created_at) VALUES (?, ?) "
            "ON CONFLICT(chat_id) DO NOTHING",
            (chat_id, _utcnow()),
        )
        await db.commit()


async def get_subscriptions(chat_id: int) -> set[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT product_slug FROM subscriptions WHERE chat_id = ?", (chat_id,)
        )
        rows = await cursor.fetchall()
        return {row[0] for row in rows}


async def toggle_subscription(chat_id: int, slug: str) -> bool:
    """Toggles subscription, returns True if now subscribed, False if unsubscribed."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM subscriptions WHERE chat_id = ? AND product_slug = ?",
            (chat_id, slug),
        )
        exists = await cursor.fetchone()
        if exists:
            await db.execute(
                "DELETE FROM subscriptions WHERE chat_id = ? AND product_slug = ?",
                (chat_id, slug),
            )
            await db.commit()
            return False
        await db.execute(
            "INSERT INTO subscriptions (chat_id, product_slug) VALUES (?, ?)",
            (chat_id, slug),
        )
        await db.commit()
        return True


async def get_all_users() -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT chat_id FROM users")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def delete_user(chat_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM subscriptions WHERE chat_id = ?", (chat_id,))
        await db.execute("DELETE FROM users WHERE chat_id = ?", (chat_id,))
        await db.commit()


async def get_subscribers(slug: str) -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT chat_id FROM subscriptions WHERE product_slug = ?", (slug,)
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def get_product_state(slug: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM product_state WHERE slug = ?", (slug,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_all_product_states() -> dict[str, dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM product_state")
        rows = await cursor.fetchall()
        return {row["slug"]: dict(row) for row in rows}


async def upsert_product_state(
    slug: str, name: str, is_in_stock: bool, price_eur: float | None, quantity: int | None
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO product_state (slug, name, is_in_stock, price_eur, quantity, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                name = excluded.name,
                is_in_stock = excluded.is_in_stock,
                price_eur = excluded.price_eur,
                quantity = excluded.quantity,
                updated_at = excluded.updated_at
            """,
            (slug, name, int(is_in_stock), price_eur, quantity, _utcnow()),
        )
        await db.commit()


async def set_meta(key: str, value: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        await db.commit()


async def get_meta(key: str) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT value FROM meta WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row[0] if row else None
