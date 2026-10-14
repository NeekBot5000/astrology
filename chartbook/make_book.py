"""Make a complete book from the command line (needs ANTHROPIC_API_KEY).

Example:
  python -m chartbook.make_book --name Sam --date 1990-07-04 --time 14:30 \\
      --place "Chicago, USA" --focus love career --out sam.pdf

It also saves the chapters as JSON next to the PDF (same format as
samples/maya.json), so you can re-render the PDF later with --from-json
without paying for the writing again.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .book import render_html, render_pdf
from .location import lookup_place, timezone_at
from .reading import FOCUS_AREAS, write_book
from .sample import load_book


def main() -> None:
    p = argparse.ArgumentParser(prog="make_book", description="Write and render a personalized birth-chart book.")
    p.add_argument("--from-json", help="re-render an existing book JSON instead of writing a new one")
    p.add_argument("--name")
    p.add_argument("--date", help="YYYY-MM-DD")
    p.add_argument("--time", help="HH:MM local time; omit if unknown")
    p.add_argument("--place", help="birth place name (needs internet)")
    p.add_argument("--lat", type=float)
    p.add_argument("--lon", type=float)
    p.add_argument("--focus", nargs="*", default=[], choices=sorted(FOCUS_AREAS))
    p.add_argument("--dedication")
    p.add_argument("--out", required=True, help="output PDF path")
    a = p.parse_args()

    out = Path(a.out)
    if a.from_json:
        book_json = Path(a.from_json)
    else:
        if not (a.name and a.date and (a.place or (a.lat is not None and a.lon is not None))):
            p.error("--name, --date and --place (or --lat/--lon) are required")
        if a.place:
            place = lookup_place(a.place)
            lat, lon, tz, place_name = place.latitude, place.longitude, place.tz_name, place.name
        else:
            lat, lon = a.lat, a.lon
            tz, place_name = timezone_at(lat, lon), f"{lat:.3f}, {lon:.3f}"
        record = {
            "name": a.name,
            "birth": {"date": a.date, "time": a.time, "place": place_name, "latitude": lat, "longitude": lon, "tz": tz},
            "focus": a.focus,
            "dedication": a.dedication,
            "chapters": [],
        }
        book_json = out.with_suffix(".json")
        book_json.write_text(json.dumps(record, indent=2))
        draft = load_book(book_json)  # computes chart + facts exactly as the renderer will

        import anthropic

        print(f"Writing 7 chapters for {a.name}...")
        chapters = write_book(anthropic.Anthropic(), draft.facts, a.name, set(a.focus))
        record["chapters"] = [c.model_dump() for c in chapters]
        book_json.write_text(json.dumps(record, indent=2))
        print(f"Saved text to {book_json}")

    render_pdf(render_html(load_book(book_json)), out)
    print(f"Saved book to {out}")


if __name__ == "__main__":
    main()
