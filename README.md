# Astrology Birth-Chart Book

A web product that turns a person's birth date, time and place into a personalized birth-chart reading, delivered as a downloadable PDF book (aimed at birthday gifts).

- Project plan: [PROJECT_BRIEF.md](PROJECT_BRIEF.md)
- Instructions for Claude Code: [CLAUDE.md](CLAUDE.md)
- Progress log: [PROGRESS.md](PROGRESS.md)

- Founder forecast: [docs/FORECAST.md](docs/FORECAST.md)

Status: milestone 1 (birth-chart calculator) done. Next: chart wheel image.

## Try the calculator
```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/python -m chartbook 1879-03-14 11:30 --lat 48.4011 --lon 9.9876 --utc-offset 0.6658
.venv/bin/python -m chartbook 1990-07-04 14:30 --place "Chicago, USA"   # needs internet
.venv/bin/python -m pytest
```

Entertainment and self-reflection only.
