"""Smoke-test the AI writer on three tricky charts (needs ANTHROPIC_API_KEY; costs roughly $0.25).

Run:  python scripts/check_writer.py
Writes one chapter per chart and prints whether it passed the citation/style checks,
how many attempts it needed, and what it cost. Chapters are saved to output/check_*.json.
"""

import json
import sys
import time as clock
from datetime import date, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import anthropic  # noqa: E402

from chartbook import compute_chart  # noqa: E402
from chartbook.facts import chart_facts  # noqa: E402
from chartbook.reading import CHAPTERS, Usage, WriterError, write_chapter  # noqa: E402

CASES = [
    ("Known time (New York, 1988)", "Jordan", compute_chart(date(1988, 11, 2), time(23, 15), 40.71, -74.01, tz_name="America/New_York"), "love"),
    ("Unknown time (Lagos, 2001)", "Ada", compute_chart(date(2001, 3, 9), None, 6.52, 3.38, tz_name="Africa/Lagos"), "big_three"),
    ("Polar birth (Tromsø, 1975)", "Sigrid", compute_chart(date(1975, 12, 21), time(6, 5), 69.65, 18.96, tz_name="Europe/Oslo"), "work"),
]


def main() -> None:
    client = anthropic.Anthropic()
    out = Path("output")
    out.mkdir(exist_ok=True)
    total = Usage()
    for label, name, chart, key in CASES:
        spec = next(s for s in CHAPTERS if s.key == key)
        facts = chart_facts(chart, name)
        usage = Usage()
        start = clock.monotonic()
        try:
            chapter = write_chapter(client, spec, facts, name, {"love", "career", "growth"}, usage=usage)
            status = f"PASSED in {usage.requests} attempt(s)"
            (out / f"check_{key}.json").write_text(json.dumps(chapter.model_dump(), indent=2))
        except WriterError as e:
            status = f"FAILED: {e}"
        for k in ("input", "output", "cache_write", "cache_read", "requests"):
            setattr(total, k, getattr(total, k) + getattr(usage, k))
        print(f"{label:32} {spec.title:28} {status}  ({clock.monotonic() - start:.0f}s, ${usage.dollars:.3f})")
    print(f"Total: ${total.dollars:.2f}. A full book is 7 chapters, so expect about {7 / len(CASES):.1f}x one chapter's cost per book.")
    print("Now READ the saved chapters in output/: do they feel specific, warm and honest?")


if __name__ == "__main__":
    main()
