"""Write the book's chapters with Claude, grounded in chart facts.

How it works, in plain terms:
1. `chart_facts` turns the chart into numbered facts ("sun", "moon_trine_venus", ...).
2. For each chapter we send Claude the style rules, ALL the facts, and the
   chapter's brief. Claude must answer in a fixed JSON shape where every
   paragraph lists the fact IDs it is based on.
3. We check the answer: unknown IDs, uncited paragraphs or a chapter that
   ignores its core facts get sent back once with the problems listed.

Cost: the style rules and the facts are identical for every chapter of one
book, so they are cached after the first chapter and re-read at ~10% price.
Expect very roughly $0.30-$0.80 per full book with the default model.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, ValidationError

from .chart import SIGNS as _SIGN_NAMES
from .facts import Fact

MODEL = "claude-opus-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"

FOCUS_AREAS = {"love", "career", "growth"}


class Paragraph(BaseModel):
    model_config = ConfigDict(extra="forbid")
    heading: str  # short subheading, or "" for none
    text: str
    cites: list[str]


class Chapter(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    opening: str  # one original sentence that sets the tone
    paragraphs: list[Paragraph]


@dataclass(frozen=True)
class ChapterSpec:
    key: str
    title: str
    brief: str
    topics: frozenset[str]
    focus: str | None = None  # which customer focus area makes this chapter longer


CHAPTERS = [
    ChapterSpec(
        "big_three", "Your Core Self",
        "Introduce the reader through the Sun, Moon and Ascendant (or just Sun and Moon if the "
        "birth time is unknown), the chart ruler and the element balance. Show how these pieces "
        "agree or pull against each other in everyday life.",
        frozenset({"identity"}),
    ),
    ChapterSpec(
        "mind", "How You Think and Speak",
        "Mercury and anything in the 3rd and 9th houses: how the reader learns, argues, decides "
        "and communicates, with concrete everyday examples.",
        frozenset({"mind"}),
    ),
    ChapterSpec(
        "love", "Love and Connection",
        "Venus, Mars, the Moon's needs and the 5th, 7th and 8th houses: what the reader is drawn "
        "to, how they show affection, and the patterns that trip them up in relationships.",
        frozenset({"love", "values"}), focus="love",
    ),
    ChapterSpec(
        "work", "Work, Money and Calling",
        "The Midheaven, Saturn, the 2nd, 6th and 10th houses and the Sun's house: the kind of "
        "work that energizes the reader, how they handle money and responsibility, and what "
        "they may want to be known for. No specific financial or career predictions.",
        frozenset({"work", "purpose", "values"}), focus="career",
    ),
    ChapterSpec(
        "inner", "Home and Inner World",
        "The Moon, the 4th and 12th houses and Neptune: what makes the reader feel safe, their "
        "private emotional habits, and how they recharge.",
        frozenset({"home", "emotions"}),
    ),
    ChapterSpec(
        "growth", "Tensions and Growth",
        "The squares and oppositions, Saturn, Pluto, Mars and any missing element: the reader's "
        "recurring inner conflicts, described honestly, and practical ways people with this "
        "pattern grow through them.",
        frozenset({"growth", "drive"}), focus="growth",
    ),
    ChapterSpec(
        "path", "Your Direction",
        "The North Node, Jupiter and the strongest themes from the whole chart: a warm, "
        "grounded closing chapter about the direction of growth this chart suggests.",
        frozenset({"purpose"}),
    ),
]

SYSTEM_PROMPT = """\
You write chapters of a personalized birth-chart book. It is sold as a gift for
entertainment and self-reflection. Each reader has paid for something that feels
written for them alone, so specificity is the whole product.

You receive a numbered list of facts computed from the reader's real birth chart.
Those facts are your only source.

Grounding rules (these are checked automatically):
- Every paragraph must list in "cites" the IDs of the facts it is based on, using
  the exact IDs given. Cite only facts the paragraph actually uses.
- Do not state any placement, aspect or house that is not in the facts.
- Mention the placement behind each paragraph in plain words at least once, so the
  reader can see why it applies to them (for example "With your Moon in the 4th
  house..."). Never show fact IDs or exact orbs in the text.
- When combining two facts, say how they interact. Combinations are where the
  reading becomes personal; prefer them over describing placements one at a time.

Writing rules:
- Address the reader as "you". Warm, intelligent, plain English (American spelling).
  Short paragraphs of 70-140 words.
- Make it concrete: describe recognizable everyday situations (how they act in an
  argument, on a Sunday, at a new job) rather than abstract adjectives.
- Be honest. Include real tensions and blind spots, framed kindly with practical
  suggestions. A reading that only flatters feels generic.
- Avoid filler and cliches: no "journey", "tapestry", "embrace", "unlock",
  "cosmic dance", "the universe has a plan", and no openers like "As a Leo...".
- Present astrology as a lens for reflection, not fate. Never predict or advise on
  health, illness, death, pregnancy, legal matters, or specific money decisions.
- Write original prose. Do not quote or imitate published horoscope books.
- "opening" is one original sentence that sets the chapter's tone.
- Use "heading" for a short subheading when a paragraph starts a new idea, otherwise "".
"""


def facts_block(facts: list[Fact], name: str | None) -> str:
    who = f"The reader's first name is {name}.\n" if name else ""
    lines = "\n".join(f"[{f.id}] {f.text}" for f in facts)
    return f"{who}Chart facts:\n{lines}"


MAX_CORE_ASPECTS = 6
BANNED_PHRASES = ["journey", "tapestry", "embrace", "unlock", "cosmic dance", "the universe has a plan", "as a "]
MIN_WORDS, MAX_WORDS = 40, 180  # per paragraph; the prompt asks for 70-140


def core_facts(spec: ChapterSpec, facts: list[Fact]) -> list[str]:
    """The facts a chapter should lean on: matching placements and summaries, plus the tightest matching aspects."""
    matching = [f for f in facts if f.topics & spec.topics]
    aspects = [f.id for f in matching if f.kind == "aspect"][:MAX_CORE_ASPECTS]  # facts list aspects tightest first
    return [f.id for f in matching if f.kind != "aspect"] + aspects


def chapter_request(spec: ChapterSpec, facts: list[Fact], focus: set[str]) -> str:
    core = core_facts(spec, facts)
    is_focus = spec.focus in focus
    length = "7-9 paragraphs (this is one of the reader's chosen focus areas)" if is_focus else "4-6 paragraphs"
    return (
        f'Write the chapter "{spec.title}".\n'
        f"Brief: {spec.brief}\n"
        f"Core facts for this chapter (use most of them; you may also draw on others): {', '.join(core)}\n"
        f"Length: {length}."
    )


def validate(chapter: Chapter, spec: ChapterSpec, facts: list[Fact]) -> list[str]:
    known = {f.id for f in facts}
    core = set(core_facts(spec, facts))
    problems = []
    if len(chapter.paragraphs) < 3:
        problems.append("The chapter needs at least 3 paragraphs.")
    for i, p in enumerate(chapter.paragraphs, 1):
        if not p.cites:
            problems.append(f"Paragraph {i} cites no facts.")
        unknown = [c for c in p.cites if c not in known]
        if unknown:
            problems.append(f"Paragraph {i} cites unknown IDs: {', '.join(unknown)}.")
        words = len(p.text.split())
        if not MIN_WORDS <= words <= MAX_WORDS:
            problems.append(f"Paragraph {i} has {words} words; aim for 70-140.")
        lowered = p.text.lower()
        for phrase in BANNED_PHRASES:
            if phrase == "as a ":
                hit = any(lowered.startswith(f"as a {sign.lower()}") for sign in _SIGN_NAMES)
            else:
                hit = phrase in lowered
            if hit:
                problems.append(f"Paragraph {i} uses the banned phrase {phrase.strip()!r}.")
    cited = {c for p in chapter.paragraphs for c in p.cites}
    if core and not cited & core:
        problems.append("The chapter does not use any of its core facts.")
    return problems


class WriterError(RuntimeError):
    pass


def write_chapter(
    client,
    spec: ChapterSpec,
    facts: list[Fact],
    name: str | None = None,
    focus: set[str] | None = None,
    model: str = MODEL,
) -> Chapter:
    """Ask Claude for one chapter and return it once it passes validation."""
    focus = focus or set()
    messages = [{
        "role": "user",
        "content": [
            # Identical for every chapter of this book -> cached after chapter 1.
            {"type": "text", "text": facts_block(facts, name), "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": chapter_request(spec, facts, focus)},
        ],
    }]
    schema = Chapter.model_json_schema()

    for attempt in range(2):
        response = client.beta.messages.create(
            model=model,
            max_tokens=16000,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=messages,
            output_config={"effort": "high", "format": {"type": "json_schema", "schema": schema}},
            betas=[FALLBACK_BETA],
            fallbacks="default",
        )
        if response.stop_reason == "refusal":
            raise WriterError(f"Model declined to write {spec.key!r}")
        if response.stop_reason == "max_tokens":
            raise WriterError(f"Chapter {spec.key!r} was cut off (max_tokens)")
        text = next(b.text for b in response.content if b.type == "text")
        try:
            chapter = Chapter.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValidationError) as e:
            raise WriterError(f"Chapter {spec.key!r} came back malformed: {e}") from e

        problems = validate(chapter, spec, facts)
        if not problems:
            return chapter
        if attempt == 0:
            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": "Please fix these problems and rewrite the whole chapter:\n- " + "\n- ".join(problems),
            })
    raise WriterError(f"Chapter {spec.key!r} failed validation: {problems}")


def write_book(client, facts: list[Fact], name: str | None, focus: set[str]) -> list[Chapter]:
    unknown = focus - FOCUS_AREAS
    if unknown:
        raise ValueError(f"Unknown focus areas: {unknown}")
    return [write_chapter(client, spec, facts, name, focus) for spec in CHAPTERS]
