"""Orders, stored in a small SQLite database file.

We keep birth details only as long as needed to make and deliver the book,
then delete them (see `purge`). No payment details are ever stored here;
Stripe handles cards.
"""

from __future__ import annotations

import secrets
import sqlite3
from dataclasses import dataclass, fields
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL,
    name TEXT,
    email TEXT,
    birth_date TEXT,
    birth_time TEXT,
    place_name TEXT,
    latitude REAL,
    longitude REAL,
    tz TEXT,
    focus TEXT,
    dedication TEXT,
    stripe_session TEXT,
    error TEXT,
    pdf_path TEXT,
    ready_at TEXT
);
"""

# preview -> (awaiting_payment -> paid | preorder) -> writing -> ready | failed ; any -> deleted
STATUSES = {"preview", "awaiting_payment", "preorder", "paid", "writing", "ready", "failed", "deleted"}
PERSONAL = ("name", "email", "birth_date", "birth_time", "place_name", "latitude", "longitude", "tz", "dedication")


@dataclass
class Order:
    id: str
    created_at: str
    status: str
    name: str | None = None
    email: str | None = None
    birth_date: str | None = None
    birth_time: str | None = None
    place_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    tz: str | None = None
    focus: str | None = None
    dedication: str | None = None
    stripe_session: str | None = None
    error: str | None = None
    pdf_path: str | None = None
    ready_at: str | None = None

    @property
    def focus_set(self) -> set[str]:
        return set(filter(None, (self.focus or "").split(",")))


def now() -> datetime:
    return datetime.now(timezone.utc)


class Store:
    def __init__(self, path: Path | str):
        self.path = str(path)
        with self._conn() as c:
            c.executescript(SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def create(self, **values) -> Order:
        order = Order(id=secrets.token_urlsafe(16), created_at=now().isoformat(), status="preview", **values)
        cols = [f.name for f in fields(Order)]
        with self._conn() as c:
            c.execute(
                f"INSERT INTO orders ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
                [getattr(order, k) for k in cols],
            )
        return order

    def get(self, order_id: str) -> Order | None:
        with self._conn() as c:
            row = c.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        return Order(**dict(row)) if row else None

    def update(self, order_id: str, **values) -> None:
        if "status" in values and values["status"] not in STATUSES:
            raise ValueError(values["status"])
        allowed = {f.name for f in fields(Order)} - {"id", "created_at"}
        bad = set(values) - allowed
        if bad:
            raise ValueError(f"Unknown fields: {bad}")
        sets = ", ".join(f"{k} = ?" for k in values)
        with self._conn() as c:
            c.execute(f"UPDATE orders SET {sets} WHERE id = ?", [*values.values(), order_id])

    def claim(self, order_id: str, from_statuses: tuple[str, ...], to_status: str) -> bool:
        """Move an order between statuses only if it is currently in one of from_statuses (no double work)."""
        marks = ", ".join("?" for _ in from_statuses)
        with self._conn() as c:
            cur = c.execute(
                f"UPDATE orders SET status = ? WHERE id = ? AND status IN ({marks})",
                [to_status, order_id, *from_statuses],
            )
        return cur.rowcount == 1

    def erase(self, order_id: str) -> None:
        """Delete personal data and the PDF, keep an anonymous row for counting sales."""
        order = self.get(order_id)
        if order and order.pdf_path:
            Path(order.pdf_path).unlink(missing_ok=True)
        self.update(order_id, status="deleted", pdf_path=None, **{k: None for k in PERSONAL})

    def purge(self, keep_days: int) -> int:
        """Erase finished orders after keep_days and abandoned previews after 2 days."""
        cutoff_ready = (now() - timedelta(days=keep_days)).isoformat()
        cutoff_preview = (now() - timedelta(days=2)).isoformat()
        with self._conn() as c:
            ids = [r["id"] for r in c.execute(
                "SELECT id FROM orders WHERE (status IN ('ready', 'failed') AND COALESCE(ready_at, created_at) < ?) "
                "OR (status IN ('preview', 'awaiting_payment') AND created_at < ?)",
                (cutoff_ready, cutoff_preview),
            )]
        for i in ids:
            self.erase(i)
        return len(ids)

    def counts(self) -> dict[str, int]:
        with self._conn() as c:
            return {r["status"]: r["n"] for r in c.execute("SELECT status, COUNT(*) AS n FROM orders GROUP BY status")}
