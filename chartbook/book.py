"""Assemble a finished book: HTML from a template, then PDF through headless Chromium."""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .chart import Chart
from .facts import HOUSE_THEME, Fact, ordinal
from .reading import CHAPTERS, Chapter
from .wheel import render_wheel

HERE = Path(__file__).parent
BRAND = "Skyprint"  # check the trademark and domain before using publicly

_env = Environment(
    loader=FileSystemLoader(HERE / "templates"),
    autoescape=select_autoescape(["html"]),
    trim_blocks=True,
    lstrip_blocks=True,
)
_env.filters["ordinal"] = ordinal

NUMBER_WORDS = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten"]


@dataclass
class BookInput:
    name: str
    chart: Chart
    facts: list[Fact]
    chapters: list[Chapter]
    birth_place: str
    birth_date: date
    birth_time_text: str  # e.g. "8:40 am" or "time unknown"
    dedication: str | None = None
    created: date = field(default_factory=date.today)


def _fonts_css() -> str:
    """Inline the bundled fonts as data URIs so the PDF never depends on the network."""
    css = (HERE / "static/fonts/fonts.css").read_text()

    def embed(m: re.Match) -> str:
        data = base64.b64encode((HERE / "static/fonts" / m.group(1)).read_bytes()).decode()
        return f"url(data:font/woff2;base64,{data})"

    return re.sub(r"url\(([\w.-]+\.woff2)\)", embed, css)


def placement_rows(chart: Chart) -> list[dict]:
    rows = []
    for p in [chart.ascendant, chart.midheaven, *chart.placements]:
        if p is None:
            continue
        d = int(p.degree_in_sign)
        m = int((p.degree_in_sign - d) * 60)
        rows.append({
            "body": p.body,
            "sign": p.sign,
            "degree": f"{d}°{m:02d}′",
            "house": p.house if p.body not in ("Ascendant", "Midheaven") else None,
            "retrograde": p.retrograde,
        })
    return rows


def render_html(book: BookInput) -> str:
    labels = {f.id: f.label for f in book.facts}
    chapters = []
    for i, (spec, ch) in enumerate(zip(CHAPTERS, book.chapters)):
        chapters.append({
            "number": NUMBER_WORDS[i],
            "title": ch.title,
            "opening": ch.opening,
            "paragraphs": [
                {"heading": p.heading, "text": p.text, "sources": [labels[c] for c in p.cites if c in labels]}
                for p in ch.paragraphs
            ],
        })
    template = _env.get_template("book.html")
    return template.render(
        brand=BRAND,
        name=book.name,
        title=f"{book.name}’s Skyprint",
        birth_date=f"{book.birth_date.day} {book.birth_date:%B %Y}",
        birth_time=book.birth_time_text,
        birth_place=book.birth_place,
        dedication=book.dedication,
        created=f"{book.created.day} {book.created:%B %Y}",
        time_known=book.chart.time_known,
        notes=book.chart.notes,
        cover_wheel=render_wheel(book.chart, 600, f"{book.name}'s chart", palette="night"),
        wheel=render_wheel(book.chart, 600, f"{book.name}'s birth chart wheel"),
        rows=placement_rows(book.chart),
        house_theme=HOUSE_THEME,
        chapters=chapters,
        fonts_css=_fonts_css(),
    )


def render_pdf(html: str, out_path: str | Path) -> Path:
    from .browser import chromium

    out = Path(out_path)
    with chromium() as browser:
        page = browser.new_page()
        page.set_content(html, wait_until="load")
        page.pdf(path=str(out), prefer_css_page_size=True, print_background=True)
    return out
