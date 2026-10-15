"""Command line: print a birth chart.

Examples:
  python -m chartbook 1990-07-04 14:30 --place "Chicago, USA"
  python -m chartbook 1879-03-14 11:30 --lat 48.4 --lon 9.983 --utc-offset 0.666
  python -m chartbook 1990-07-04 unknown --place "Chicago, USA" --json
"""

import argparse
import json
from datetime import date, time

from .chart import compute_chart
from .location import lookup_place, timezone_at


def main() -> None:
    p = argparse.ArgumentParser(prog="chartbook", description="Calculate a birth chart.")
    p.add_argument("date", help="birth date, YYYY-MM-DD")
    p.add_argument("time", help="local birth time HH:MM, or 'unknown'")
    p.add_argument("--place", help="birth place name (needs internet)")
    p.add_argument("--lat", type=float)
    p.add_argument("--lon", type=float)
    p.add_argument("--tz", help="IANA time zone, e.g. Europe/London (looked up if omitted)")
    p.add_argument("--utc-offset", type=float, help="override: hours ahead of UTC at birth")
    p.add_argument("--houses", choices=["placidus", "whole_sign"], default="placidus")
    p.add_argument("--json", action="store_true", help="print JSON instead of text")
    a = p.parse_args()

    if a.place:
        place = lookup_place(a.place)
        lat, lon, tz = place.latitude, place.longitude, a.tz or place.tz_name
        print(f"Place: {place.name} ({lat:.4f}, {lon:.4f}, {tz})")
    elif a.lat is not None and a.lon is not None:
        lat, lon = a.lat, a.lon
        tz = a.tz or (None if a.utc_offset is not None else timezone_at(lat, lon))
    else:
        p.error("give --place, or both --lat and --lon")

    birth_time = None if a.time.lower() == "unknown" else time.fromisoformat(a.time)
    chart = compute_chart(
        date.fromisoformat(a.date), birth_time, lat, lon,
        tz_name=tz, utc_offset_hours=a.utc_offset, house_system=a.houses,
    )

    if a.json:
        print(json.dumps(chart.to_dict(), indent=2))
        return

    print(f"UTC: {chart.utc:%Y-%m-%d %H:%M}")
    for pl in [chart.ascendant, chart.midheaven, *chart.placements]:
        if pl:
            house = f"  house {pl.house}" if pl.house else ""
            print(f"  {pl.label}{house}")
    print("Aspects:")
    for asp in chart.aspects:
        print(f"  {asp.body1} {asp.kind} {asp.body2} (orb {asp.orb}°)")
    for note in chart.notes:
        print(f"Note: {note}")


if __name__ == "__main__":
    main()
