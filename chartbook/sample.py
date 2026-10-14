"""Load a hand-written or saved book from JSON (see samples/maya.json)."""

import json
from datetime import date, datetime, time
from pathlib import Path

from .book import BookInput
from .chart import compute_chart
from .facts import chart_facts
from .reading import Chapter


def time_text(t: time | None) -> str:
    return datetime.combine(date.today(), t).strftime("%-I:%M %p").lower() if t else "time unknown"


def load_book(path: str | Path) -> BookInput:
    d = json.loads(Path(path).read_text())
    b = d["birth"]
    birth_date = date.fromisoformat(b["date"])
    birth_time = time.fromisoformat(b["time"]) if b.get("time") else None
    chart = compute_chart(birth_date, birth_time, b["latitude"], b["longitude"], tz_name=b["tz"])
    return BookInput(
        name=d["name"],
        chart=chart,
        facts=chart_facts(chart, d["name"]),
        chapters=[Chapter.model_validate(c) for c in d["chapters"]],
        birth_place=b["place"],
        birth_date=birth_date,
        birth_time_text=time_text(birth_time),
        dedication=d.get("dedication"),
    )
