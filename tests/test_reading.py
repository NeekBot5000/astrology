import json
import xml.etree.ElementTree as ET
from datetime import date, time
from types import SimpleNamespace

import pytest

from chartbook import compute_chart
from chartbook.facts import chart_facts
from chartbook.reading import CHAPTERS, Chapter, WriterError, chapter_request, validate, write_chapter
from chartbook.wheel import render_wheel


@pytest.fixture(scope="module")
def einstein():
    return compute_chart(date(1879, 3, 14), time(11, 30), 48.4011, 9.9876, utc_offset_hours=0.6658)


@pytest.fixture(scope="module")
def facts(einstein):
    return chart_facts(einstein, "Albert")


def test_fact_ids_are_unique_and_cover_the_chart(facts):
    ids = [f.id for f in facts]
    assert len(ids) == len(set(ids))
    for body in ("sun", "moon", "ascendant", "midheaven", "north_node", "chart_ruler", "balance"):
        assert body in ids
    ruler = next(f for f in facts if f.id == "chart_ruler")
    assert "Moon" in ruler.text and "Cancer" in ruler.text
    assert any(f.id == "stellium" and "House 10 holds 4" in f.text for f in facts)


def test_unknown_time_facts_have_no_houses():
    chart = compute_chart(date(1990, 7, 4), None, 41.88, -87.63, tz_name="America/Chicago")
    facts = chart_facts(chart)
    ids = {f.id for f in facts}
    assert "ascendant" not in ids and "chart_ruler" not in ids and "stellium" not in ids
    assert not any("house" in f.text.lower() and f.id in {"sun", "moon"} for f in facts)
    assert any(f.id.startswith("note_") for f in facts)


def test_every_chapter_has_core_facts(facts):
    for spec in CHAPTERS:
        req = chapter_request(spec, facts, set())
        core = req.split("Core facts for this chapter")[1].split("\n")[0]
        assert core.count(",") >= 1, spec.key


def _chapter(cites_per_para):
    return {
        "title": "Love and Connection",
        "opening": "Some hearts move fast.",
        "paragraphs": [{"heading": "", "text": "x " * 80, "cites": c} for c in cites_per_para],
    }


class FakeClient:
    """Stands in for anthropic.Anthropic(); returns queued JSON answers."""

    def __init__(self, *answers, stop_reason="end_turn"):
        self.answers = list(answers)
        self.calls = []
        self.stop_reason = stop_reason
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        block = SimpleNamespace(type="text", text=json.dumps(self.answers.pop(0)))
        return SimpleNamespace(stop_reason=self.stop_reason, content=[block])


LOVE = next(s for s in CHAPTERS if s.key == "love")


def test_validate_flags_uncited_and_unknown(facts):
    ch = Chapter.model_validate(_chapter([["venus"], [], ["made_up"]]))
    problems = validate(ch, LOVE, facts)
    assert any("Paragraph 2 cites no facts" in p for p in problems)
    assert any("made_up" in p for p in problems)


def test_write_chapter_accepts_valid_answer_and_caches_prompt(facts):
    client = FakeClient(_chapter([["venus"], ["mars", "mars_trine_pluto"], ["moon_trine_venus"]]))
    chapter = write_chapter(client, LOVE, facts, "Albert", {"love"})
    assert chapter.title == "Love and Connection"
    call = client.calls[0]
    assert call["model"] == "claude-opus-5-5"
    assert call["system"][0]["cache_control"] == {"type": "ephemeral"}
    facts_part, ask_part = call["messages"][0]["content"]
    assert facts_part["cache_control"] == {"type": "ephemeral"}
    assert "[venus]" in facts_part["text"] and "Albert" in facts_part["text"]
    assert "7-9 paragraphs" in ask_part["text"]
    assert call["output_config"]["format"]["type"] == "json_schema"


def test_write_chapter_retries_once_with_problems(facts):
    bad = _chapter([["venus"], [], ["nope"]])
    good = _chapter([["venus"], ["mars"], ["moon_trine_venus"]])
    client = FakeClient(bad, good)
    write_chapter(client, LOVE, facts)
    assert len(client.calls) == 2
    feedback = client.calls[1]["messages"][-1]["content"]
    assert "Paragraph 2 cites no facts" in feedback and "nope" in feedback


def test_write_chapter_gives_up_after_second_failure(facts):
    bad = _chapter([[], [], []])
    with pytest.raises(WriterError, match="failed validation"):
        write_chapter(FakeClient(bad, bad), LOVE, facts)


def test_refusal_raises(facts):
    with pytest.raises(WriterError, match="declined"):
        write_chapter(FakeClient(_chapter([["venus"]] * 3), stop_reason="refusal"), LOVE, facts)


def test_wheel_is_valid_svg_with_all_bodies(einstein):
    svg = render_wheel(einstein, 600, "Albert's chart")
    root = ET.fromstring(svg)
    ns = "{http://www.w3.org/2000/svg}"
    titles = [t.text for t in root.iter(f"{ns}title")]
    assert titles[0] == "Albert's chart"
    for p in einstein.placements:
        assert p.label in titles
    texts = [t.text for t in root.iter(f"{ns}text")]
    assert "AC" in texts and "MC" in texts
    assert [str(h) for h in range(1, 13)] == [t for t in texts if t and t.isdigit()][:12]


def test_wheel_without_birth_time_has_no_houses():
    chart = compute_chart(date(1990, 7, 4), None, 41.88, -87.63, tz_name="America/Chicago")
    texts = [t.text for t in ET.fromstring(render_wheel(chart)).iter("{http://www.w3.org/2000/svg}text")]
    assert "AC" not in texts
    assert not any(t and t.isdigit() for t in texts)
