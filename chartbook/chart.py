"""Birth-chart calculation.

Turns a birth moment (local date and time, time zone, latitude, longitude) into
planet positions, houses and aspects using the Swiss Ephemeris.

Plain-language notes:
- Longitude here means "position around the zodiac circle", 0-360 degrees,
  where 0 is the start of Aries, 30 the start of Taurus, and so on.
- We use the Swiss Ephemeris' built-in "Moshier" mode, which needs no extra
  data files and is accurate to well under a second of arc for the planets
  over the years people are born in. That is far finer than astrology needs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import swisseph as swe

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

BODIES = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
    "North Node": swe.TRUE_NODE,
}

# Angle between two bodies -> aspect name, and how far off exact still counts (orb).
ASPECTS = [
    ("conjunction", 0, 8),
    ("sextile", 60, 4),
    ("square", 90, 7),
    ("trine", 120, 7),
    ("opposition", 180, 8),
]
# The Sun and Moon traditionally get a wider orb.
LUMINARY_ORB_BONUS = 2

FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED


class BirthTimeError(ValueError):
    """The local birth time does not exist or happened twice (daylight-saving change)."""


@dataclass
class Placement:
    body: str
    longitude: float
    sign: str
    degree_in_sign: float
    retrograde: bool
    house: int | None

    @property
    def label(self) -> str:
        # Round to the arcminute first so 29°59.7' shows as 0°00' of the next sign.
        minutes = round(self.longitude * 60) % (360 * 60)
        sign = SIGNS[minutes // (30 * 60)]
        d, m = divmod(minutes % (30 * 60), 60)
        r = " (retrograde)" if self.retrograde else ""
        return f"{self.body} {d}°{m:02d}' {sign}{r}"


@dataclass
class Aspect:
    body1: str
    body2: str
    kind: str
    orb: float  # degrees away from exact


@dataclass
class Chart:
    utc: datetime
    latitude: float
    longitude: float
    time_known: bool
    house_system: str | None
    placements: list[Placement]
    ascendant: Placement | None
    midheaven: Placement | None
    house_cusps: list[float] | None
    aspects: list[Aspect]
    notes: list[str] = field(default_factory=list)

    def get(self, body: str) -> Placement:
        for p in self.placements:
            if p.body == body:
                return p
        raise KeyError(body)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["utc"] = self.utc.isoformat()
        return d


def sign_of(longitude: float) -> tuple[str, float]:
    longitude %= 360
    return SIGNS[int(longitude // 30)], longitude % 30


def to_utc(
    birth_date: date,
    birth_time: time,
    tz_name: str | None = None,
    utc_offset_hours: float | None = None,
) -> datetime:
    """Convert a local birth time to UTC.

    Use tz_name (an IANA zone such as "America/New_York") in normal cases; it knows
    historical daylight-saving rules. Use utc_offset_hours to override it when the
    real offset is known to differ, e.g. pre-1900 local mean time in a small town.
    """
    local = datetime.combine(birth_date, birth_time)
    if utc_offset_hours is not None:
        return (local - timedelta(hours=utc_offset_hours)).replace(tzinfo=timezone.utc)
    if tz_name is None:
        raise ValueError("Give either tz_name or utc_offset_hours")

    zone = ZoneInfo(tz_name)
    early = local.replace(tzinfo=zone, fold=0)
    late = local.replace(tzinfo=zone, fold=1)
    if early.utcoffset() != late.utcoffset():
        # Clocks jumped here. If converting there and back changes the time,
        # it never existed (spring forward); otherwise it happened twice (fall back).
        roundtrip = early.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)
        if roundtrip != local:
            raise BirthTimeError(
                f"{local} did not exist in {tz_name} (clocks jumped forward)."
            )
        raise BirthTimeError(
            f"{local} happened twice in {tz_name} (clocks went back). "
            "Pass utc_offset_hours to say which one."
        )
    return early.astimezone(timezone.utc)


def _julian_day(utc: datetime) -> float:
    hours = utc.hour + utc.minute / 60 + utc.second / 3600 + utc.microsecond / 3.6e9
    return swe.julday(utc.year, utc.month, utc.day, hours, swe.GREG_CAL)


def _house_of(longitude: float, cusps: list[float]) -> int:
    for i in range(12):
        start, end = cusps[i], cusps[(i + 1) % 12]
        span = (end - start) % 360
        if (longitude - start) % 360 < span:
            return i + 1
    return 12


def _find_aspects(placements: list[Placement]) -> list[Aspect]:
    found = []
    for i, a in enumerate(placements):
        for b in placements[i + 1:]:
            sep = abs(a.longitude - b.longitude) % 360
            sep = min(sep, 360 - sep)
            for kind, angle, orb in ASPECTS:
                allowed = orb
                if {a.body, b.body} & {"Sun", "Moon"}:
                    allowed += LUMINARY_ORB_BONUS
                if a.body == "North Node" or b.body == "North Node":
                    allowed = min(allowed, 3)
                off = abs(sep - angle)
                if off <= allowed:
                    found.append(Aspect(a.body, b.body, kind, round(off, 2)))
                    break
    return sorted(found, key=lambda x: x.orb)


def compute_chart(
    birth_date: date,
    birth_time: time | None,
    latitude: float,
    longitude: float,
    tz_name: str | None = None,
    utc_offset_hours: float | None = None,
    house_system: str = "placidus",
) -> Chart:
    """Calculate a natal chart.

    birth_time=None means the time is unknown: we use local noon, skip houses and
    the ascendant (they change every few minutes), and warn that the Moon may be
    off by up to about 6-7 degrees.
    """
    notes = []
    time_known = birth_time is not None
    utc = to_utc(birth_date, birth_time or time(12, 0), tz_name, utc_offset_hours)
    jd = _julian_day(utc)

    cusps = asc = mc = None
    used_system = None
    if time_known:
        hsys = {"placidus": b"P", "whole_sign": b"W"}[house_system]
        used_system = house_system
        try:
            raw_cusps, ascmc = swe.houses(jd, latitude, longitude, hsys)
        except swe.Error:
            raw_cusps = None
        # Placidus breaks down near the poles; Swiss Ephemeris then falls back on its
        # own or returns nonsense. Above the polar circles use whole-sign houses.
        if raw_cusps is None or (hsys == b"P" and abs(latitude) > 66.0):
            raw_cusps, ascmc = swe.houses(jd, latitude, longitude, b"W")
            used_system = "whole_sign"
            notes.append("Placidus houses do not work this close to the poles; used whole-sign houses.")
        cusps = [round(c, 6) for c in raw_cusps[:12]]
        asc_lon, mc_lon = ascmc[0], ascmc[1]
    else:
        notes.append(
            "Birth time unknown: houses, ascendant and midheaven are left out, "
            "and the Moon's position may be off by up to about 7 degrees."
        )

    placements = []
    for name, body in BODIES.items():
        pos, _ = swe.calc_ut(jd, body, FLAGS)
        lon, speed = pos[0] % 360, pos[3]
        sign, deg = sign_of(lon)
        placements.append(Placement(
            body=name,
            longitude=round(lon, 6),
            sign=sign,
            degree_in_sign=round(deg, 6),
            retrograde=speed < 0 and name not in ("Sun", "Moon", "North Node"),
            house=_house_of(lon, cusps) if cusps else None,
        ))

    if time_known:
        asc = Placement("Ascendant", round(asc_lon, 6), *sign_of(asc_lon), False, 1)
        mc = Placement("Midheaven", round(mc_lon, 6), *sign_of(mc_lon), False, _house_of(mc_lon, cusps))

    return Chart(
        utc=utc,
        latitude=latitude,
        longitude=longitude,
        time_known=time_known,
        house_system=used_system,
        placements=placements,
        ascendant=asc,
        midheaven=mc,
        house_cusps=cusps,
        aspects=_find_aspects(placements),
        notes=notes,
    )
