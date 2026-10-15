"""Orders, stored in a small SQLite database file.

We keep birth details only as long as needed to make and deliver the book,
then delete them (see `purge`). No payment details are ever stored here;
Stripe handles cards.
"""

from __future__ import annotations

import secrets
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
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
    ready_at TEXT,
    source TEXT,
    reserved_at TEXT,
    checkout_at TEXT,
    paid_at TEXT,
    cost_cents INTEGER,
    consent_at TEXT
);
CREATE TABLE IF NOT EXISTS visits (
    day TEXT NOT NULL,
    source TEXT NOT NULL,
    n INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (day, source)
);
"""

# preview -> (awaiting_payment -> paid | preorder) -> writing -> [review ->] ready | failed ; any -> deleted
STATUSES = {"preview", "awaiting_payment", "preorder", "paid", "writing", "review", "ready", "failed", "deleted"}
PREORDER_DAYS = 120
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
    source: str | None = None  # marketing link tag, e.g. "tiktok"
    reserved_at: str | None = None  # when they reserved a copy (pre-order mode)
    checkout_at: str | None = None  # when they last went to the payment page
    paid_at: str | None = None  # kept after erasing, so sales stay countable
    cost_cents: int | None = None  # AI writing cost for this book
    consent_at: str | None = None  # when the buyer accepted the terms and immediate delivery (kept as evidence)

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
            # Add columns that older databases don't have yet.
            cols = {r["name"] for r in c.execute("PRAGMA table_info(orders)")}
            for col, kind in (("source", "TEXT"), ("reserved_at", "TEXT"), ("checkout_at", "TEXT"),
                              ("paid_at", "TEXT"), ("cost_cents", "INTEGER"), ("consent_at", "TEXT")):
                if col not in cols:
                    c.execute(f"ALTER TABLE orders ADD COLUMN {col} {kind}")

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        """A connection that commits on success, rolls back on error, and always closes."""
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

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
        """Erase finished orders after keep_days, abandoned previews after 2 days and reservations after 120 days."""
        cutoff_ready = (now() - timedelta(days=keep_days)).isoformat()
        cutoff_preview = (now() - timedelta(days=2)).isoformat()
        cutoff_preorder = (now() - timedelta(days=PREORDER_DAYS)).isoformat()
        with self._conn() as c:
            ids = [r["id"] for r in c.execute(
                "SELECT id FROM orders WHERE (status IN ('ready', 'failed') AND COALESCE(ready_at, created_at) < ?) "
                "OR (status = 'preview' AND reserved_at IS NULL AND created_at < ?) "
                # Abandoned checkout: Stripe sessions expire after 24 hours, so 2 days is safe.
                "OR (status = 'awaiting_payment' AND reserved_at IS NULL AND COALESCE(checkout_at, created_at) < ?) "
                # Reservations (even ones that later started a checkout) are kept for PREORDER_DAYS.
                "OR (status IN ('preorder', 'awaiting_payment') AND reserved_at IS NOT NULL AND reserved_at < ?)",
                (cutoff_ready, cutoff_preview, cutoff_preview, cutoff_preorder),
            )]
        for i in ids:
            self.erase(i)
        return len(ids)

    def count_visit(self, source: str) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO visits (day, source, n) VALUES (?, ?, 1) "
                "ON CONFLICT(day, source) DO UPDATE SET n = n + 1",
                (now().date().isoformat(), source),
            )

    def paid_count(self, since: str | None = None) -> int:
        with self._conn() as c:
            return c.execute("SELECT COUNT(*) FROM orders WHERE paid_at IS NOT NULL AND created_at >= ?", (since or "0000",)).fetchone()[0]

    def funnel(self, since: str | None = None) -> list[dict]:
        """Visitors, previews, reservations and paid orders per link tag."""
        since = since or "0000"
        rows: dict[str, dict] = {}

        def row(src):
            return rows.setdefault(src or "direct", {"source": src or "direct", "visits": 0, "previews": 0, "preorders": 0, "paid": 0})

        with self._conn() as c:
            for r in c.execute("SELECT source, SUM(n) AS n FROM visits WHERE day >= ? GROUP BY source", (since[:10],)):
                row(r["source"])["visits"] = r["n"]
            for r in c.execute(
                "SELECT source, COUNT(*) AS previews, COUNT(reserved_at) AS preorders, COUNT(paid_at) AS paid "
                "FROM orders WHERE created_at >= ? GROUP BY source", (since,)
            ):
                x = row(r["source"])
                x["previews"] += r["previews"]
                x["preorders"] += r["preorders"]
                x["paid"] += r["paid"]
        return sorted(rows.values(), key=lambda x: (-x["paid"], -x["visits"]))

    def with_status(self, status: str) -> list[Order]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM orders WHERE status = ? ORDER BY created_at", (status,)).fetchall()
        return [Order(**dict(r)) for r in rows]

    def preorders(self) -> list[Order]:
        return self.with_status("preorder")

    def average_cost_cents(self) -> float | None:
        with self._conn() as c:
            return c.execute("SELECT AVG(cost_cents) FROM orders WHERE cost_cents IS NOT NULL").fetchone()[0]

    def counts(self, since: str | None = None) -> dict[str, int]:
        """Orders per status, optionally only those created on or after `since` (ISO date)."""
        query, args = "SELECT status, COUNT(*) AS n FROM orders", []
        if since:
            query += " WHERE created_at >= ?"
            args.append(since)
        with self._conn() as c:
            return {r["status"]: r["n"] for r in c.execute(query + " GROUP BY status", args)}
