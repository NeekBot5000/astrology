"""Original line-drawn astrological glyphs as SVG path data on a 24x24 grid.

Drawn as strokes (no fill) so one stroke width styles them all. Drawing them
ourselves avoids font differences and emoji rendering of the Unicode symbols.
"""


def _circle(cx: float, cy: float, r: float) -> str:
    return f"M{cx - r} {cy} a{r} {r} 0 1 0 {2 * r} 0 a{r} {r} 0 1 0 {-2 * r} 0"


SIGN_GLYPHS = {
    "Aries": "M12 21 V9 M12 9 C12 3 4 2.5 4 8 C4 10 5 11 6.5 11 M12 9 C12 3 20 2.5 20 8 C20 10 19 11 17.5 11",
    "Taurus": _circle(12, 15, 5) + " M4 4 C5 8 8 10 12 10 C16 10 19 8 20 4",
    "Gemini": "M5 4 C9 6 15 6 19 4 M5 20 C9 18 15 18 19 20 M9 5.4 V18.6 M15 5.4 V18.6",
    "Cancer": "M19.5 8.5 C17 4.5 9 4 7.5 6 " + _circle(7.5, 8.5, 2.5)
              + " M4.5 15.5 C7 19.5 15 20 16.5 18 " + _circle(16.5, 15.5, 2.5),
    "Leo": _circle(8, 15.5, 2.5) + " M10.5 15.5 C10.5 11 8 9 9 6 C10 3 16 3 16 7 C16 11 12.5 14 13 17.5 C13.5 20.5 16.5 20.5 18.5 18.5",
    "Virgo": "M4 7 V18 M4 9.5 C4 6 9 6 9 9.5 V18 M9 9.5 C9 6 14 6 14 9.5 V17 C14 20.5 19.5 20 19.5 15 C19.5 11.5 15.5 12 14 15",
    "Libra": "M4 20 H20 M4 16 H8.5 C6 13 8 7 12 7 C16 7 18 13 15.5 16 H20",
    "Scorpio": "M4 7 V18 M4 9.5 C4 6 9 6 9 9.5 V18 M9 9.5 C9 6 14 6 14 9.5 V17 C14 19.5 16.5 19.5 19.5 17 M16.8 16 L19.5 17 L18.6 19.8",
    "Sagittarius": "M5 19 L19 5 M12.5 5 H19 V11.5 M8 11 L13 16",
    "Capricorn": "M3.5 6.5 C5.5 6 7 7.5 7 10 V18 M7 10 C7 6 12 6 12 10 V15 C12 20 18.5 20 18.5 16 C18.5 13 14.5 12.5 13.3 15 C12.3 17.5 10.5 20 8 20.5",
    "Aquarius": "M3 10 L6 7 L9 10 L12 7 L15 10 L18 7 L21 10 M3 17 L6 14 L9 17 L12 14 L15 17 L18 14 L21 17",
    "Pisces": "M5 4 C10 8 10 16 5 20 M19 4 C14 8 14 16 19 20 M6.5 12 H17.5",
}

BODY_GLYPHS = {
    "Sun": _circle(12, 12, 7.5) + " " + _circle(12, 12, 1),
    "Moon": "M15 3.5 A8.5 8.5 0 1 0 15 20.5 A7 7 0 1 1 15 3.5 Z",
    "Mercury": _circle(12, 11, 4) + " M8 3.5 C8.5 6.5 15.5 6.5 16 3.5 M12 15 V22 M9 19 H15",
    "Venus": _circle(12, 8.5, 5) + " M12 13.5 V22 M8.5 18.5 H15.5",
    "Mars": _circle(9, 15, 5) + " M12.5 11.5 L19.5 4.5 M14 4.5 H19.5 V10",
    "Jupiter": "M5 8 C5 3.5 11.5 3.5 10.5 8 C9.5 11 6.5 14 4 16 H18.5 M14.5 4 V21",
    "Saturn": "M7 3 V16 M4 6 H10 M7 11.5 C8 8 15 8 15 12 C15 15 11 16 11 19 C11 21 13 21.5 14.5 20",
    "Uranus": _circle(12, 16, 5) + " " + _circle(12, 16, 1) + " M12 11 V3 M9 6 L12 3 L15 6",
    "Neptune": "M5 5 C5 12 8 14 12 14 C16 14 19 12 19 5 M12 3 V21 M8.5 18 H15.5",
    "Pluto": "M5 5 C5 12.5 19 12.5 19 5 " + _circle(12, 6.5, 2.5) + " M12 11.5 V21 M8.5 17.5 H15.5",
    "North Node": "M7 16 C3 12 5 5 12 5 C19 5 21 12 17 16 " + _circle(7, 18, 2) + " " + _circle(17, 18, 2),
}
