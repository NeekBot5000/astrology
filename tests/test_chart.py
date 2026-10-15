from datetime import date, datetime, time, timezone

import pytest

from chartbook import BirthTimeError, compute_chart, to_utc
from chartbook.location import timezone_at


def arc_diff(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def test_einstein_matches_published_chart():
    # Albert Einstein, 14 March 1879, 11:30 local mean time, Ulm (birth record).
    # Ulm's local mean time is UTC+0:39:57, which no IANA zone knows, hence the override.
    # Reference values are the widely published chart (Astrodatabank, Rodden AA).
    chart = compute_chart(
        date(1879, 3, 14), time(11, 30), 48.4011, 9.9876, utc_offset_hours=0.6658
    )
    expected = {
        "Sun": ("Pisces", 23.5),
        "Moon": ("Sagittarius", 14.53),
        "Mercury": ("Aries", 3.15),
        "Venus": ("Aries", 16.98),
        "Mars": ("Capricorn", 26.92),
        "Jupiter": ("Aquarius", 27.48),
        "Saturn": ("Aries", 4.18),
    }
    for body, (sign, deg) in expected.items():
        p = chart.get(body)
        assert p.sign == sign, body
        assert abs(p.degree_in_sign - deg) < 0.1, body
    assert chart.ascendant.sign == "Cancer"
    assert abs(chart.ascendant.degree_in_sign - 11.63) < 0.25
    assert chart.midheaven.sign == "Pisces"
    assert chart.get("Sun").house == 10


def test_sun_at_2024_march_equinox_is_zero_aries():
    # Equinox was 2024-03-20 03:06 UTC: the Sun crosses 0 degrees Aries.
    chart = compute_chart(date(2024, 3, 20), time(3, 6), 0, 0, tz_name="UTC")
    assert arc_diff(chart.get("Sun").longitude, 0) < 0.01
    assert chart.get("Sun").label.startswith("Sun 0°00' Aries")


def test_sun_at_2025_june_solstice_is_zero_cancer():
    # Solstice was 2025-06-21 02:42 UTC.
    chart = compute_chart(date(2025, 6, 21), time(2, 42), 0, 0, tz_name="UTC")
    assert arc_diff(chart.get("Sun").longitude, 90) < 0.01


def test_daylight_saving_is_applied_historically():
    # US Eastern time was on daylight saving (UTC-4) in July 1990, standard (UTC-5) in January.
    assert to_utc(date(1990, 7, 4), time(12, 0), "America/New_York") == datetime(1990, 7, 4, 16, 0, tzinfo=timezone.utc)
    assert to_utc(date(1990, 1, 4), time(12, 0), "America/New_York") == datetime(1990, 1, 4, 17, 0, tzinfo=timezone.utc)
    # The UK kept clocks one hour ahead all year from 1968 to 1971 (British Standard Time).
    assert to_utc(date(1970, 1, 15), time(12, 0), "Europe/London") == datetime(1970, 1, 15, 11, 0, tzinfo=timezone.utc)


def test_nonexistent_and_ambiguous_local_times_are_rejected():
    with pytest.raises(BirthTimeError, match="did not exist"):
        to_utc(date(2021, 3, 14), time(2, 30), "America/New_York")
    with pytest.raises(BirthTimeError, match="happened twice"):
        to_utc(date(2021, 11, 7), time(1, 30), "America/New_York")
    # The caller can settle an ambiguous time by giving the offset.
    assert to_utc(date(2021, 11, 7), time(1, 30), utc_offset_hours=-4).hour == 5


def test_unknown_birth_time_skips_houses():
    chart = compute_chart(date(1990, 7, 4), None, 41.88, -87.63, tz_name="America/Chicago")
    assert chart.ascendant is None and chart.house_cusps is None
    assert all(p.house is None for p in chart.placements)
    assert chart.get("Sun").sign == "Cancer"
    assert any("unknown" in n for n in chart.notes)


def test_polar_birth_falls_back_to_whole_sign_houses():
    # Tromsø, Norway, about 69.6 degrees north.
    chart = compute_chart(date(2000, 6, 1), time(12, 0), 69.65, 18.96, tz_name="Europe/Oslo")
    assert chart.house_system == "whole_sign"
    assert all(1 <= p.house <= 12 for p in chart.placements)


def test_every_planet_lands_in_exactly_one_house():
    chart = compute_chart(date(1985, 10, 26), time(9, 15), 34.05, -118.24, tz_name="America/Los_Angeles")
    assert len(chart.house_cusps) == 12
    for p in chart.placements:
        assert 1 <= p.house <= 12
    assert chart.ascendant.house == 1


def test_aspects_are_within_orb_and_sorted():
    chart = compute_chart(date(1985, 10, 26), time(9, 15), 34.05, -118.24, tz_name="America/Los_Angeles")
    orbs = [a.orb for a in chart.aspects]
    assert orbs == sorted(orbs)
    assert all(o <= 10 for o in orbs)


def test_timezone_lookup_is_offline():
    assert timezone_at(48.4011, 9.9876) == "Europe/Berlin"
    assert timezone_at(40.7128, -74.006) == "America/New_York"
