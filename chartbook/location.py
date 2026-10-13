"""Turn a birth place name into latitude, longitude and time zone.

Geocoding (looking up a place name) uses OpenStreetMap's free Nominatim service,
so it needs an internet connection. The time-zone lookup works offline.
"""

from __future__ import annotations

from dataclasses import dataclass

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


def lookup_place(query: str) -> Place:
    from geopy.geocoders import Nominatim

    geocoder = Nominatim(user_agent="chartbook-birth-chart")
    hit = geocoder.geocode(query, language="en")
    if hit is None:
        raise LookupError(f"Could not find a place called {query!r}")
    return Place(hit.address, hit.latitude, hit.longitude, timezone_at(hit.latitude, hit.longitude))
