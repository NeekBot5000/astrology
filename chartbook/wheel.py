"""Draw a birth chart as an SVG zodiac wheel.

Layout follows the usual Western convention: the Ascendant sits on the left
(9 o'clock) and the zodiac runs counter-clockwise. Without a birth time, 0° Aries
goes on the left and no houses are drawn.

Glyphs are drawn as SVG paths (see glyphs.py), so the image looks the same in
every browser and PDF without depending on installed fonts.
"""

from __future__ import annotations

import math
from xml.sax.saxutils import escape

from .chart import SIGNS, Chart
from .facts import ELEMENT
from .glyphs import BODY_GLYPHS, SIGN_GLYPHS

ELEMENT_FILL = {"fire": "#f6e3d8", "earth": "#e6eadb", "air": "#e8e6f2", "water": "#dde9ef"}
ASPECT_STYLE = {
    "conjunction": None,  # drawn as overlap, no line
    "trine": ("#3b7d6e", ""),
    "sextile": ("#3b7d6e", "4 3"),
    "square": ("#b2533e", ""),
    "opposition": ("#b2533e", "8 3"),
}
INK = "#2b2a33"
MUTED = "#8a8794"


def _polar(cx: float, cy: float, r: float, angle_deg: float) -> tuple[float, float]:
    a = math.radians(angle_deg)
    return cx + r * math.cos(a), cy - r * math.sin(a)


def _spread(longitudes: list[float], min_gap: float) -> list[float]:
    """Nudge display positions apart so glyphs don't overlap; true positions are kept separately."""
    if not longitudes:
        return []
    order = sorted(range(len(longitudes)), key=lambda i: longitudes[i])
    pos = [longitudes[i] for i in order]
    for _ in range(50):
        moved = False
        for k in range(len(pos)):
            nxt = (k + 1) % len(pos)
            if len(pos) == 1:
                break
            gap = (pos[nxt] - pos[k]) % 360
            if gap < min_gap:
                push = (min_gap - gap) / 2
                pos[k] -= push
                pos[nxt] += push
                moved = True
        if not moved:
            break
    out = [0.0] * len(pos)
    for k, i in enumerate(order):
        out[i] = pos[k] % 360
    return out


def _glyph(path_d: str, x: float, y: float, size: float, color: str, stroke: float = 1.6) -> str:
    # Glyph paths are drawn on a 24x24 grid centered on (12, 12).
    s = size / 24
    return (
        f'<path d="{path_d}" transform="translate({x - 12 * s:.2f} {y - 12 * s:.2f}) scale({s:.4f})" '
        f'fill="none" stroke="{color}" stroke-width="{stroke / s:.2f}" stroke-linecap="round" stroke-linejoin="round"/>'
    )


def render_wheel(chart: Chart, size: int = 600, title: str | None = None) -> str:
    cx = cy = size / 2
    r_out = size * 0.452
    r_sign = size * 0.378    # inner edge of the zodiac ring
    r_planet = size * 0.325  # planet glyphs
    r_degree = size * 0.279  # degree labels
    r_house = size * 0.244   # house numbers
    r_aspect = size * 0.222  # aspect lines end here

    asc = chart.ascendant.longitude if chart.ascendant else 0.0

    def ang(lon: float) -> float:
        return 180 + (lon - asc)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}" '
        f'role="img" aria-labelledby="wheel-title">',
        f'<title id="wheel-title">{escape(title or "Birth chart wheel")}</title>',
        f'<circle cx="{cx}" cy="{cy}" r="{r_out}" fill="#fbfaf7" stroke="{INK}" stroke-width="1.5"/>',
    ]

    # Zodiac ring: 12 colored segments with sign glyphs.
    for i, sign in enumerate(SIGNS):
        a0, a1 = ang(i * 30), ang(i * 30 + 30)
        x0, y0 = _polar(cx, cy, r_out, a0)
        x1, y1 = _polar(cx, cy, r_out, a1)
        x2, y2 = _polar(cx, cy, r_sign, a1)
        x3, y3 = _polar(cx, cy, r_sign, a0)
        parts.append(
            f'<path d="M{x0:.2f},{y0:.2f} A{r_out},{r_out} 0 0 0 {x1:.2f},{y1:.2f} '
            f'L{x2:.2f},{y2:.2f} A{r_sign},{r_sign} 0 0 1 {x3:.2f},{y3:.2f} Z" '
            f'fill="{ELEMENT_FILL[ELEMENT[sign]]}" stroke="{INK}" stroke-width="0.8"/>'
        )
        gx, gy = _polar(cx, cy, (r_out + r_sign) / 2, ang(i * 30 + 15))
        parts.append(_glyph(SIGN_GLYPHS[sign], gx, gy, size * 0.045, INK))
        # 5-degree ticks
        for d in range(0, 30, 5):
            t0 = _polar(cx, cy, r_sign, ang(i * 30 + d))
            t1 = _polar(cx, cy, r_sign + (size * 0.012 if d else size * 0.02), ang(i * 30 + d))
            parts.append(f'<line x1="{t0[0]:.2f}" y1="{t0[1]:.2f}" x2="{t1[0]:.2f}" y2="{t1[1]:.2f}" stroke="{INK}" stroke-width="0.6"/>')

    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r_sign}" fill="#ffffff" stroke="{INK}" stroke-width="1"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r_aspect}" fill="none" stroke="{MUTED}" stroke-width="0.6"/>')

    # Houses
    if chart.house_cusps:
        for h, cusp in enumerate(chart.house_cusps, 1):
            angle_line = h in (1, 4, 7, 10)
            p0 = _polar(cx, cy, r_aspect, ang(cusp))
            p1 = _polar(cx, cy, r_out if angle_line else r_sign, ang(cusp))
            parts.append(
                f'<line x1="{p0[0]:.2f}" y1="{p0[1]:.2f}" x2="{p1[0]:.2f}" y2="{p1[1]:.2f}" '
                f'stroke="{INK if angle_line else MUTED}" stroke-width="{1.6 if angle_line else 0.7}"/>'
            )
            nxt = chart.house_cusps[h % 12]
            mid = cusp + ((nxt - cusp) % 360) / 2
            tx, ty = _polar(cx, cy, r_house, ang(mid))
            parts.append(
                f'<text x="{tx:.2f}" y="{ty:.2f}" font-size="{size * 0.022:.1f}" fill="{MUTED}" '
                f'text-anchor="middle" dominant-baseline="central" font-family="Helvetica, Arial, sans-serif">{h}</text>'
            )
        for label, lon in (("AC", asc), ("MC", chart.midheaven.longitude)):
            lx, ly = _polar(cx, cy, r_out + size * 0.028, ang(lon))
            parts.append(
                f'<text x="{lx:.2f}" y="{ly:.2f}" font-size="{size * 0.024:.1f}" fill="{INK}" font-weight="600" '
                f'text-anchor="middle" dominant-baseline="central" font-family="Helvetica, Arial, sans-serif">{label}</text>'
            )

    # Aspect lines
    lon_of = {p.body: p.longitude for p in chart.placements}
    for a in chart.aspects:
        style = ASPECT_STYLE[a.kind]
        if style is None:
            continue
        color, dash = style
        p0 = _polar(cx, cy, r_aspect, ang(lon_of[a.body1]))
        p1 = _polar(cx, cy, r_aspect, ang(lon_of[a.body2]))
        opacity = max(0.35, 1 - a.orb / 8)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        parts.append(
            f'<line x1="{p0[0]:.2f}" y1="{p0[1]:.2f}" x2="{p1[0]:.2f}" y2="{p1[1]:.2f}" '
            f'stroke="{color}" stroke-width="1.1" stroke-opacity="{opacity:.2f}"{dash_attr}/>'
        )

    # Planets: tick at true position, glyph at spread-out position.
    bodies = chart.placements
    shown = _spread([p.longitude for p in bodies], min_gap=7.5)
    for p, disp in zip(bodies, shown):
        t0 = _polar(cx, cy, r_sign, ang(p.longitude))
        t1 = _polar(cx, cy, r_sign - size * 0.018, ang(p.longitude))
        parts.append(f'<line x1="{t0[0]:.2f}" y1="{t0[1]:.2f}" x2="{t1[0]:.2f}" y2="{t1[1]:.2f}" stroke="{INK}" stroke-width="1.4"/>')
        g = _polar(cx, cy, r_planet, ang(disp))
        dot = _polar(cx, cy, r_aspect, ang(p.longitude))
        parts.append(f'<circle cx="{dot[0]:.2f}" cy="{dot[1]:.2f}" r="{size * 0.005:.2f}" fill="{INK}"/>')
        parts.append(f'<g><title>{escape(p.label)}</title>{_glyph(BODY_GLYPHS[p.body], g[0], g[1], size * 0.045, INK, 1.7)}</g>')
        deg = _polar(cx, cy, r_degree, ang(disp))
        retro = "r" if p.retrograde else ""
        parts.append(
            f'<text x="{deg[0]:.2f}" y="{deg[1]:.2f}" font-size="{size * 0.019:.1f}" fill="{MUTED}" '
            f'text-anchor="middle" dominant-baseline="central" font-family="Helvetica, Arial, sans-serif">'
            f"{int(p.degree_in_sign)}°{retro}</text>"
        )

    parts.append("</svg>")
    return "\n".join(parts)
