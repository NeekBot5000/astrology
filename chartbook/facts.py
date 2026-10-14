"""Turn a computed chart into a list of plain facts with stable IDs.

The writer (an AI model) only ever sees these facts, and must cite their IDs for
every paragraph. That is how we keep the reading specific and traceable instead
of generic horoscope filler.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .chart import Chart, Placement

ELEMENT = {
    "Aries": "fire", "Leo": "fire", "Sagittarius": "fire",
    "Taurus": "earth", "Virgo": "earth", "Capricorn": "earth",
    "Gemini": "air", "Libra": "air", "Aquarius": "air",
    "Cancer": "water", "Scorpio": "water", "Pisces": "water",
}
MODALITY = {
    "Aries": "cardinal", "Cancer": "cardinal", "Libra": "cardinal", "Capricorn": "cardinal",
    "Taurus": "fixed", "Leo": "fixed", "Scorpio": "fixed", "Aquarius": "fixed",
    "Gemini": "mutable", "Virgo": "mutable", "Sagittarius": "mutable", "Pisces": "mutable",
}
RULER = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Pluto",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Uranus", "Pisces": "Neptune",
}
HOUSE_THEME = {
    1: "self-image, body and first impressions",
    2: "money, possessions and self-worth",
    3: "communication, learning, siblings and neighborhood",
    4: "home, family, roots and private life",
    5: "creativity, romance, play and children",
    6: "daily work, routines, health habits and service",
    7: "partnerships, marriage and close one-to-one relationships",
    8: "intimacy, shared resources, crisis and transformation",
    9: "travel, higher learning, beliefs and big-picture meaning",
    10: "career, public reputation and ambition",
    11: "friends, communities, hopes and future plans",
    12: "solitude, the unconscious, endings and inner life",
}
BODY_THEME = {
    "Sun": "core identity and life force",
    "Moon": "emotions, needs and instinctive reactions",
    "Mercury": "thinking, speaking and learning style",
    "Venus": "love, attraction, taste and values",
    "Mars": "drive, anger, courage and desire",
    "Jupiter": "growth, luck, generosity and optimism",
    "Saturn": "discipline, fear, responsibility and lessons learned slowly",
    "Uranus": "independence, sudden change and originality",
    "Neptune": "dreams, intuition, idealism and confusion",
    "Pluto": "power, obsession and deep transformation",
    "North Node": "the direction of growth that feels unfamiliar but rewarding",
    "Ascendant": "outer manner, first impressions and approach to new things",
    "Midheaven": "public role, vocation and what one wants to be known for",
}
ASPECT_THEME = {
    "conjunction": "fused together, acting as one",
    "sextile": "easy cooperation that rewards effort",
    "square": "friction that pushes for action",
    "trine": "natural, effortless flow",
    "opposition": "a tug-of-war that seeks balance",
}
# Slower outer planets move so little that whole generations share their sign;
# only their house and aspects are personal.
GENERATIONAL = {"Uranus", "Neptune", "Pluto"}


@dataclass(frozen=True)
class Fact:
    id: str
    text: str
    topics: frozenset[str]
    kind: str = "placement"  # "placement", "aspect" or "summary"
    label: str = ""  # short reader-facing source line, e.g. "Venus in Gemini, 12th house"


def ordinal(n: int) -> str:
    return f"{n}{'th' if 11 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _slug(name: str) -> str:
    return name.lower().replace(" ", "_")


def _placement_fact(p: Placement) -> Fact:
    deg = int(p.degree_in_sign)
    parts = [f"{p.body} at {deg}° {p.sign}"]
    if p.retrograde:
        parts.append("retrograde")
    if p.house:
        parts.append(f"in house {p.house} ({HOUSE_THEME[p.house]})")
    text = ", ".join(parts) + f". {p.body} governs {BODY_THEME[p.body]}."
    text += f" {p.sign} is a {MODALITY[p.sign]} {ELEMENT[p.sign]} sign."
    if p.body in GENERATIONAL:
        text += " Its sign is shared by everyone born within several years, so stress its house and aspects."
    if 29 <= p.degree_in_sign or p.degree_in_sign < 1:
        text += " It sits right at the edge of a sign, a point astrologers treat as a threshold."
    if p.body == "Ascendant":
        label = f"{p.sign} rising"
    else:
        label = f"{p.body} in {p.sign}" + (f", {ordinal(p.house)} house" if p.house and p.body != "Midheaven" else "")
    return Fact(_slug(p.body), text, _topics_for(p.body, p.house), label=label)


def _topics_for(body: str, house: int | None) -> frozenset[str]:
    topics = {
        "Sun": {"identity", "purpose"}, "Moon": {"identity", "emotions", "home"},
        "Mercury": {"mind"}, "Venus": {"love", "values"}, "Mars": {"drive", "love"},
        "Jupiter": {"growth", "purpose"}, "Saturn": {"growth", "work"},
        "Uranus": {"growth"}, "Neptune": {"growth", "emotions"}, "Pluto": {"growth"},
        "North Node": {"purpose", "growth"}, "Ascendant": {"identity"}, "Midheaven": {"work", "purpose"},
    }.get(body, set()).copy()
    topics |= {
        1: {"identity"}, 2: {"values", "work"}, 3: {"mind"}, 4: {"home", "emotions"},
        5: {"love"}, 6: {"work"}, 7: {"love"}, 8: {"love", "growth"},
        9: {"mind", "purpose"}, 10: {"work", "purpose"}, 11: {"purpose"}, 12: {"emotions", "growth"},
    }.get(house, set())
    return frozenset(topics)


def chart_facts(chart: Chart, name: str | None = None) -> list[Fact]:
    facts: list[Fact] = []
    angles = [a for a in (chart.ascendant, chart.midheaven) if a]
    for p in angles + chart.placements:
        facts.append(_placement_fact(p))

    # Who "rules" the chart: the planet linked to the rising sign.
    if chart.ascendant:
        ruler = RULER[chart.ascendant.sign]
        rp = chart.get(ruler)
        where = f" in house {rp.house}" if rp.house else ""
        facts.append(Fact(
            "chart_ruler",
            f"Chart ruler: {ruler} (rules the {chart.ascendant.sign} Ascendant), placed in {rp.sign}{where}. "
            "The chart ruler colors the whole personality.",
            frozenset({"identity", "purpose"}),
            kind="summary",
            label=f"Chart ruler: {ruler}",
        ))

    personal = [p for p in chart.placements if p.body != "North Node"]
    elements = Counter(ELEMENT[p.sign] for p in personal)
    modes = Counter(MODALITY[p.sign] for p in personal)
    el_text = ", ".join(f"{elements.get(e, 0)} {e}" for e in ("fire", "earth", "air", "water"))
    mode_text = ", ".join(f"{modes.get(m, 0)} {m}" for m in ("cardinal", "fixed", "mutable"))
    strongest = elements.most_common(1)[0][0]
    missing = [e for e in ("fire", "earth", "air", "water") if elements.get(e, 0) == 0]
    text = f"Element balance of the ten planets: {el_text}. Strongest element: {strongest}."
    if missing:
        text += f" No planets in {', '.join(missing)}, which astrologers read as something to consciously develop."
    text += f" Modality balance: {mode_text}."
    facts.append(Fact("balance", text, frozenset({"identity", "growth"}), kind="summary", label="Element balance"))

    if chart.house_cusps:
        houses = Counter(p.house for p in personal)
        busy = [h for h, n in houses.most_common() if n >= 3]
        if busy:
            facts.append(Fact(
                "stellium",
                "; ".join(f"House {h} holds {houses[h]} planets ({HOUSE_THEME[h]})" for h in busy)
                + ". A crowded house is a major life focus.",
                frozenset().union(*(_topics_for("", h) for h in busy)),
                kind="summary",
                label="Crowded " + " and ".join(f"{ordinal(h)} house" for h in busy),
            ))

    for a in chart.aspects:
        if a.body1 in GENERATIONAL and a.body2 in GENERATIONAL:
            continue  # shared by everyone born within years of each other; not personal
        tight = "very tight" if a.orb < 1.5 else ("close" if a.orb < 4 else "wide")
        topics = _topics_for(a.body1, None) | _topics_for(a.body2, None)
        facts.append(Fact(
            f"{_slug(a.body1)}_{a.kind}_{_slug(a.body2)}",
            f"{a.body1} {a.kind} {a.body2} ({tight}, {a.orb}° from exact): {ASPECT_THEME[a.kind]}, "
            f"linking {BODY_THEME[a.body1]} with {BODY_THEME[a.body2]}.",
            frozenset(topics),
            kind="aspect",
            label=f"{a.body1} {a.kind} {a.body2}",
        ))

    for i, note in enumerate(chart.notes, 1):
        facts.append(Fact(f"note_{i}", note, frozenset({"identity"}), kind="summary", label="Chart note"))
    return facts
