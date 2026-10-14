import json
import os
import re
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from chartbook.location import Place
from chartbook.web.app import create_app
from chartbook.web.config import load_settings

PORTLAND = Place("Portland, Oregon, United States", 45.5152, -122.6784, "America/Los_Angeles")
HAS_BROWSER = bool(os.environ.get("CHROMIUM_PATH"))

FORM = {"name": "Sam", "birth_date": "1994-05-17", "birth_time": "08:40", "place": "Portland", "focus": ["love"]}


class FakeWriter:
    """Answers every chapter request with a valid chapter citing its first core facts."""

    def __init__(self):
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))
        self.calls = 0

    def _create(self, **kw):
        self.calls += 1
        ask = kw["messages"][0]["content"][1]["text"]
        title = re.search(r'Write the chapter "(.+?)"', ask).group(1)
        core = re.search(r"you may also draw on others\): (.+)", ask).group(1).split(", ")
        para = {"heading": "A heading", "text": "word " * 90, "cites": core[:2]}
        body = {"title": title, "opening": "An opening line.", "paragraphs": [para, para, para]}
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=json.dumps(body))])


class FakeStripe:
    def __init__(self):
        self.created = []
        self.paid = True
        sessions = SimpleNamespace(create=self._create, retrieve=self._retrieve)
        self.v1 = SimpleNamespace(checkout=SimpleNamespace(sessions=sessions))

    def _create(self, params):
        self.created.append(params)
        return SimpleNamespace(id="cs_test_1", url="https://checkout.stripe.test/cs_test_1")

    def _retrieve(self, session_id):
        return SimpleNamespace(id=session_id, payment_status="paid" if self.paid else "unpaid")

    def construct_event(self, payload, sig, secret):
        if sig != "good":
            raise ValueError("bad signature")
        data = json.loads(payload)
        obj = SimpleNamespace(metadata=data["metadata"], payment_status="paid")
        return SimpleNamespace(type="checkout.session.completed", data=SimpleNamespace(object=obj))


def make_client(tmp_path, monkeypatch, payments=False):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings = load_settings()
    stripe = None
    if payments:
        settings = replace(settings, stripe_secret_key="sk_test", stripe_webhook_secret="whsec")
        stripe = FakeStripe()
    writer = FakeWriter()
    app = create_app(settings, geocode=lambda q: PORTLAND, writer_client=lambda: writer, stripe_client=stripe)
    return TestClient(app), app, stripe, writer


def start_preview(client, **overrides):
    r = client.post("/preview", data={**FORM, **overrides}, follow_redirects=False)
    assert r.status_code == 303, r.text[:500]
    return r.headers["location"].rsplit("/", 1)[1]


def test_landing_page_shows_sample_and_price(tmp_path, monkeypatch):
    client, *_ = make_client(tmp_path, monkeypatch)
    r = client.get("/")
    assert r.status_code == 200
    assert "Love and Connection" in r.text and "Venus in Gemini, 12th house" in r.text
    assert "$29" in r.text
    assert r.headers["x-frame-options"] == "DENY"


def test_form_errors_are_listed(tmp_path, monkeypatch):
    client, *_ = make_client(tmp_path, monkeypatch)
    r = client.post("/preview", data={"name": "", "birth_date": "1800-01-01", "place": ""})
    assert r.status_code == 422
    assert "first name" in r.text and "between 1900 and today" in r.text and "birth time" in r.text


def test_daylight_saving_gap_is_explained(tmp_path, monkeypatch):
    client, *_ = make_client(tmp_path, monkeypatch)
    r = client.post("/preview", data={**FORM, "birth_date": "2021-03-14", "birth_time": "02:30"})
    assert r.status_code == 422 and "daylight saving" in r.text


def test_unknown_time_preview_has_no_rising_sign(tmp_path, monkeypatch):
    client, *_ = make_client(tmp_path, monkeypatch)
    order_id = start_preview(client, birth_time="", time_unknown="true")
    r = client.get(f"/p/{order_id}")
    assert "Rising sign" not in r.text and "time unknown" in r.text and "two of the" in r.text


def test_preorder_mode_records_email(tmp_path, monkeypatch):
    client, app, *_ = make_client(tmp_path, monkeypatch)
    order_id = start_preview(client)
    page = client.get(f"/p/{order_id}")
    assert "Rising sign" in page.text and "Reserve my copy" in page.text and "8:40 am" in page.text
    r = client.post(f"/p/{order_id}/checkout", data={"email": "sam@example.com"})
    assert r.status_code == 200 and "You're on the list" in r.text
    assert app.state.store.get(order_id).status == "preorder"


def test_paid_flow_writes_book(tmp_path, monkeypatch):
    client, app, stripe, writer = make_client(tmp_path, monkeypatch, payments=True)
    if HAS_BROWSER is False:
        # Without a browser we still test everything up to rendering the PDF.
        monkeypatch.setattr("chartbook.web.pipeline.render_pdf", lambda html, out: (out.write_bytes(b"%PDF-fake"), out)[1])
    order_id = start_preview(client)
    r = client.post(f"/p/{order_id}/checkout", data={"email": "sam@example.com"}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("https://checkout.stripe.test/")
    params = stripe.created[0]
    assert params["line_items"][0]["price_data"]["unit_amount"] == 2900
    assert params["metadata"] == {"order_id": order_id}

    # Returning from Stripe triggers writing (the webhook might be slower).
    r = client.get(f"/order/{order_id}?session_id=cs_test_1")
    assert r.status_code == 200
    order = app.state.store.get(order_id)
    assert order.status == "ready", order.error
    assert writer.calls == 7
    pdf = client.get(f"/order/{order_id}/book.pdf")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")

    # A late webhook must not write the book twice.
    client.post("/stripe/webhook", content=json.dumps({"metadata": {"order_id": order_id}}), headers={"stripe-signature": "good"})
    assert writer.calls == 7

    # Erase on request.
    r = client.post(f"/order/{order_id}/delete")
    assert r.status_code == 200 and "deleted" in r.text
    gone = app.state.store.get(order_id)
    assert gone.status == "deleted" and gone.name is None and gone.birth_date is None
    assert client.get(f"/order/{order_id}").status_code == 404


def test_webhook_rejects_bad_signature_and_marks_paid(tmp_path, monkeypatch):
    client, app, stripe, writer = make_client(tmp_path, monkeypatch, payments=True)
    monkeypatch.setattr("chartbook.web.pipeline.render_pdf", lambda html, out: (out.write_bytes(b"%PDF-fake"), out)[1])
    order_id = start_preview(client)
    client.post(f"/p/{order_id}/checkout", data={}, follow_redirects=False)
    body = json.dumps({"metadata": {"order_id": order_id}})
    assert client.post("/stripe/webhook", content=body, headers={"stripe-signature": "bad"}).status_code == 400
    assert app.state.store.get(order_id).status == "awaiting_payment"
    assert client.post("/stripe/webhook", content=body, headers={"stripe-signature": "good"}).status_code == 200
    assert app.state.store.get(order_id).status == "ready"


def test_unpaid_return_does_not_start_writing(tmp_path, monkeypatch):
    client, app, stripe, writer = make_client(tmp_path, monkeypatch, payments=True)
    stripe.paid = False
    order_id = start_preview(client)
    client.post(f"/p/{order_id}/checkout", data={}, follow_redirects=False)
    client.get(f"/order/{order_id}?session_id=cs_test_1")
    assert app.state.store.get(order_id).status == "awaiting_payment" and writer.calls == 0
    # A forged session id is ignored too.
    stripe.paid = True
    client.get(f"/order/{order_id}?session_id=cs_someone_else")
    assert app.state.store.get(order_id).status == "awaiting_payment"


def test_writer_failure_lands_on_order(tmp_path, monkeypatch):
    client, app, stripe, writer = make_client(tmp_path, monkeypatch, payments=True)
    writer.beta.messages.create = lambda **kw: SimpleNamespace(stop_reason="refusal", content=[])
    order_id = start_preview(client)
    client.post(f"/p/{order_id}/checkout", data={}, follow_redirects=False)
    r = client.get(f"/order/{order_id}?session_id=cs_test_1")
    assert app.state.store.get(order_id).status == "failed"
    assert "Something went wrong" in client.get(f"/order/{order_id}").text


def test_purge_erases_old_orders(tmp_path, monkeypatch):
    client, app, *_ = make_client(tmp_path, monkeypatch)
    store = app.state.store
    old = start_preview(client)
    fresh = start_preview(client)
    long_ago = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    with store._conn() as c:
        c.execute("UPDATE orders SET created_at = ? WHERE id = ?", (long_ago, old))
    assert store.purge(keep_days=30) == 1
    assert store.get(old).status == "deleted" and store.get(old).name is None
    assert store.get(fresh).status == "preview"


def test_honeypot_blocks_bots(tmp_path, monkeypatch):
    client, *_ = make_client(tmp_path, monkeypatch)
    r = client.post("/preview", data={**FORM, "website": "http://spam"})
    assert r.status_code == 422


@pytest.mark.skipif(not HAS_BROWSER, reason="set CHROMIUM_PATH to render PDFs")
def test_sample_book_renders_to_pdf(tmp_path):
    from chartbook.book import render_html, render_pdf
    from chartbook.sample import load_book

    book = load_book("samples/maya.json")
    html = render_html(book)
    assert "For Maya" in html and "Venus in Gemini, 12th house" in html
    out = render_pdf(html, tmp_path / "maya.pdf")
    assert out.read_bytes().startswith(b"%PDF") and out.stat().st_size > 100_000
