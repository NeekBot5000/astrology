"""Turn a birth place name into latitude, longitude and time zone.

Geocoding (looking up a place name) uses OpenStreetMap's free Nominatim service,
so it needs an internet connection. The time-zone lookup works offline.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from timezonefinder import TimezoneFinder

_tf = TimezoneFinder()


@dataclass
class Place:
    name: str
    latitude: float
    longitude: float
    tz_name: str


def timezone_at(latitude: float, longitude: float) -> str:
    tz = _tf.timezone_at(lat=latitude, lng=longitude)
    if tz is None:
        raise LookupError(f"No time zone found for {latitude}, {longitude}")
    return tz


@lru_cache(maxsize=2048)
def lookup_place(query: str) -> Place:
    """Look up a place name. Results are cached, as OpenStreetMap's usage policy asks."""
    from geopy.geocoders import Nominatim

    # The policy asks for an identifying user agent with a contact address.
    contact = os.environ.get("SUPPORT_EMAIL", "")
    geocoder = Nominatim(user_agent=f"birth-chart-book/1.0 ({contact})" if contact else "birth-chart-book/1.0", timeout=10)
    hit = geocoder.geocode(query.strip(), language="en")
    if hit is None:
        raise LookupError(f"Could not find a place called {query!r}")
    return Place(hit.address, hit.latitude, hit.longitude, timezone_at(hit.latitude, hit.longitude))
