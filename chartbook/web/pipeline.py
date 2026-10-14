"""Turn a paid order into a finished PDF."""

from __future__ import annotations

import logging
from datetime import date, time

from ..book import BookInput, render_html, render_pdf
from ..chart import Chart, compute_chart
from ..facts import chart_facts
from ..reading import write_book
from ..sample import time_text
from .store import Order, Store, now

log = logging.getLogger(__name__)


def order_chart(order: Order) -> Chart:
    return compute_chart(
        date.fromisoformat(order.birth_date),
        time.fromisoformat(order.birth_time) if order.birth_time else None,
        order.latitude,
        order.longitude,
        tz_name=order.tz,
    )


def make_book(store: Store, order_id: str, client_factory, data_dir) -> None:
    """Write and render the book for a paid order. Safe to call twice: only one call does the work."""
    if not store.claim(order_id, ("paid",), "writing"):
        return
    order = store.get(order_id)
    try:
        chart = order_chart(order)
        facts = chart_facts(chart, order.name)
        chapters = write_book(client_factory(), facts, order.name, order.focus_set)
        book = BookInput(
            name=order.name,
            chart=chart,
            facts=facts,
            chapters=chapters,
            birth_place=order.place_name,
            birth_date=date.fromisoformat(order.birth_date),
            birth_time_text=time_text(time.fromisoformat(order.birth_time) if order.birth_time else None),
            dedication=order.dedication,
        )
        books = data_dir / "books"
        books.mkdir(exist_ok=True)
        pdf = render_pdf(render_html(book), books / f"{order.id}.pdf")
        store.update(order_id, status="ready", pdf_path=str(pdf), ready_at=now().isoformat(), error=None)
    except Exception as e:  # noqa: BLE001 - any failure must land on the order, not vanish
        log.exception("Book generation failed for %s", order_id)
        store.update(order_id, status="failed", error=f"{type(e).__name__}: {e}"[:500])
