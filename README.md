# Astrology Birth-Chart Book

A web product that turns a person's birth date, time and place into a personalized birth-chart reading, delivered as a downloadable PDF book (aimed at birthday gifts).

- Project plan: [PROJECT_BRIEF.md](PROJECT_BRIEF.md)
- Progress log: [PROGRESS.md](PROGRESS.md)
- Founder forecast: [docs/FORECAST.md](docs/FORECAST.md)
- Launch plan (pre-sale test): [docs/LAUNCH_PLAN.md](docs/LAUNCH_PLAN.md)
- Putting it online: [docs/DEPLOY.md](docs/DEPLOY.md)
- Sample book: [samples/maya-sample.pdf](samples/maya-sample.pdf) (fictional person)

Status: all five brief milestones built; ready to deploy once the owner picks a name, price and accounts (see PROGRESS.md).

## How it fits together

| Piece | File | What it does |
|---|---|---|
| Chart maths | `chartbook/chart.py` | Planet positions, houses, aspects (Swiss Ephemeris), historical time zones |
| Chart facts | `chartbook/facts.py` | Turns a chart into numbered facts the writer must cite |
| Writer | `chartbook/reading.py` | Claude writes 7 chapters as structured JSON; every paragraph's citations are checked |
| Chart wheel | `chartbook/wheel.py`, `glyphs.py` | SVG zodiac wheel with original line glyphs |
| Book | `chartbook/book.py`, `templates/book.html` | 6×9 in PDF via headless Chromium |
| Website | `chartbook/web/` | Landing page, free preview, Stripe checkout or "reserve" mode, delivery, data deletion, stats |

## Try it

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/playwright install chromium

# A chart in the terminal
.venv/bin/python -m chartbook 1879-03-14 11:30 --lat 48.4011 --lon 9.9876 --utc-offset 0.6658

# Re-render the sample book
.venv/bin/python -m chartbook.make_book --from-json samples/maya.json --out maya.pdf

# Write a brand-new book (needs ANTHROPIC_API_KEY)
.venv/bin/python -m chartbook.make_book --name Sam --date 1990-07-04 --time 14:30 --place "Chicago, USA" --focus love --out sam.pdf

# The website
.venv/bin/uvicorn chartbook.web.app:app --reload

# Tests
.venv/bin/python -m pytest
```

Entertainment and self-reflection only.
