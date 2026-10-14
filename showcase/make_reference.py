"""Write Swiss Ephemeris reference positions for random births, for showcase/check_chart.js.

Run from the repo root:
  .venv/bin/python showcase/make_reference.py > /tmp/reference.json
  npm install astronomy-engine@2.1.19   (once, anywhere on NODE_PATH)
  node showcase/check_chart.js /tmp/reference.json
"""

import json
import random
import sys
from datetime import date, datetime, time, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from chartbook import compute_chart  # noqa: E402

random.seed(7)
cases = []
for _ in range(60):
    y, m, d = random.randint(1920, 2025), random.randint(1, 12), random.randint(1, 28)
    hh, mm = random.randint(0, 23), random.randint(0, 59)
    lat, lon = random.uniform(-55, 64), random.uniform(-170, 175)
    chart = compute_chart(date(y, m, d), time(hh, mm), lat, lon, tz_name="UTC")
    cases.append({
        "utc": datetime(y, m, d, hh, mm, tzinfo=timezone.utc).isoformat(),
        "lat": lat,
        "lon": lon,
        "planets": {p.body: [p.longitude, p.retrograde] for p in chart.placements if p.body != "North Node"},
        "asc": chart.ascendant.longitude,
        "mc": chart.midheaven.longitude,
    })
print(json.dumps(cases))
