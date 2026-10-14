"""The website: landing page, free chart preview, checkout and delivery.

Run locally:  uvicorn chartbook.web.app:app --reload
"""

from __future__ import annotations

import logging
import time as _time
from collections import defaultdict, deque
from datetime import date, time
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..book import BRAND
from ..chart import BirthTimeError, compute_chart
from ..facts import HOUSE_THEME, ordinal
from ..location import lookup_place
from ..sample import time_text
from ..wheel import render_wheel
from .config import Settings, load_settings
from .pipeline import make_book
from .store import Store

log = logging.getLogger(__name__)
HERE = Path(__file__).parent
ROOT = HERE.parent.parent

SIGN_STYLE = {
    "Aries": "bold, quick to start and happiest with a challenge",
    "Taurus": "steady, sensual and loyal once committed",
    "Gemini": "curious, quick-witted and always making connections",
    "Cancer": "caring, protective and finely tuned to moods",
    "Leo": "warm, generous and made to be seen",
    "Virgo": "observant, practical and quietly devoted",
    "Libra": "fair-minded, sociable and drawn to harmony",
    "Scorpio": "intense, private and fiercely loyal",
    "Sagittarius": "adventurous, candid and always looking further",
    "Capricorn": "ambitious, patient and built for the long climb",
    "Aquarius": "independent, inventive and guided by ideals",
    "Pisces": "imaginative, empathetic and deeply intuitive",
}
FOCUS_LABELS = {"love": "Love and relationships", "career": "Work and calling", "growth": "Personal growth"}


class RateLimiter:
    """Allow `limit` actions per `window` seconds per visitor (in memory; fine for one server)."""

    def __init__(self, limit: int, window: float):
        self.limit, self.window = limit, window
        self.hits: dict[str, deque] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        t = _time.monotonic()
        q = self.hits[key]
        while q and t - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(t)
        return True


def _anthropic_client():
    import anthropic

    return anthropic.Anthropic()


def create_app(settings: Settings | None = None, geocode=lookup_place, writer_client=_anthropic_client, stripe_client=None) -> FastAPI:
    settings = settings or load_settings()
    store = Store(settings.data_dir / "orders.sqlite3")
    if stripe_client is None and settings.payments_enabled:
        import stripe

        stripe_client = stripe.StripeClient(settings.stripe_secret_key)

    app = FastAPI(title=BRAND, docs_url=None, redoc_url=None, openapi_url=None)
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
    app.mount("/fonts", StaticFiles(directory=HERE.parent / "static/fonts"), name="fonts")
    templates = Jinja2Templates(directory=HERE / "templates")
    templates.env.filters["ordinal"] = ordinal
    limiter = RateLimiter(limit=12, window=600)
    last_purge = {"t": 0.0}

    from ..sample import load_book

    sample_book = load_book(ROOT / "samples/maya.json")
    sample_chapter = next(c for c in sample_book.chapters if c.title == "Love and Connection")
    sample_labels = {f.id: f.label for f in sample_book.facts}
    sample_sources = [" · ".join(sample_labels[c] for c in p.cites) for p in sample_chapter.paragraphs]
    hero_wheel = render_wheel(sample_book.chart, 600, "Sample chart wheel", palette="night")

    landing = dict(chapter=sample_chapter, sample_sources=sample_sources, hero_wheel=hero_wheel, focus_labels=FOCUS_LABELS)

    def page(request: Request, name: str, status_code: int = 200, **ctx) -> HTMLResponse:
        ctx.update(brand=BRAND, price=settings.price_text, payments=settings.payments_enabled,
                   support_email=settings.support_email, keep_days=settings.keep_days)
        return templates.TemplateResponse(request, name, ctx, status_code=status_code)

    @app.middleware("http")
    async def housekeeping(request: Request, call_next):
        if _time.monotonic() - last_purge["t"] > 3600:
            last_purge["t"] = _time.monotonic()
            removed = store.purge(settings.keep_days)
            if removed:
                log.info("Purged %d old orders", removed)
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("X-Frame-Options", "DENY")
        return response

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request):
        return page(request, "index.html", form={}, errors=[], **landing)

    @app.post("/preview")
    def preview(
        request: Request,
        name: str = Form(""),
        birth_date: str = Form(""),
        birth_time: str = Form(""),
        time_unknown: bool = Form(False),
        place: str = Form(""),
        focus: list[str] = Form([]),
        dedication: str = Form(""),
        website: str = Form(""),  # honeypot: humans never see or fill this
    ):
        form = dict(name=name, birth_date=birth_date, birth_time=birth_time, time_unknown=time_unknown,
                    place=place, focus=focus, dedication=dedication)
        errors = []
        name = name.strip()
        if not 1 <= len(name) <= 40:
            errors.append("Please enter a first name (up to 40 characters).")
        try:
            bdate = date.fromisoformat(birth_date)
            if not date(1900, 1, 1) <= bdate <= date.today():
                errors.append("Please enter a birth date between 1900 and today.")
        except ValueError:
            bdate = None
            errors.append("Please enter the birth date.")
        btime = None
        if not time_unknown:
            try:
                btime = time.fromisoformat(birth_time)
            except ValueError:
                errors.append("Please enter the birth time, or tick “I don’t know the time”.")
        place = place.strip()
        if not 2 <= len(place) <= 120:
            errors.append("Please enter the town or city of birth.")
        focus = [f for f in focus if f in FOCUS_LABELS]
        dedication = dedication.strip()
        if len(dedication) > 300:
            errors.append("Please keep the gift note under 300 characters.")
        if website:
            errors.append("Something went wrong. Please try again.")

        def again(status: int):
            return page(request, "index.html", status_code=status, form=form, errors=errors, **landing)

        if errors:
            return again(422)
        if not limiter.allow(request.client.host if request.client else "?"):
            errors.append("Too many previews in a short time. Please wait a few minutes.")
            return again(429)
        try:
            found = geocode(place)
        except LookupError:
            errors.append(f"We couldn’t find “{place}”. Try adding the country, e.g. “Springfield, Illinois, USA”.")
            return again(422)
        except Exception:  # noqa: BLE001 - geocoder outage
            log.exception("Geocoding failed")
            errors.append("Our place lookup is having trouble. Please try again in a minute.")
            return again(503)
        try:
            compute_chart(bdate, btime, found.latitude, found.longitude, tz_name=found.tz_name)
        except BirthTimeError:
            errors.append("Clocks changed for daylight saving at that exact time, so it happened twice or not at all. "
                          "Please check the time on the birth certificate, or move it by an hour.")
            return again(422)

        order = store.create(
            name=name, birth_date=bdate.isoformat(), birth_time=btime.strftime("%H:%M") if btime else None,
            place_name=found.name, latitude=found.latitude, longitude=found.longitude, tz=found.tz_name,
            focus=",".join(focus), dedication=dedication or None,
        )
        return RedirectResponse(f"/p/{order.id}", status_code=303)

    def _order_or_404(order_id: str):
        order = store.get(order_id)
        if not order or order.status == "deleted":
            raise HTTPException(404)
        return order

    @app.get("/p/{order_id}", response_class=HTMLResponse)
    def show_preview(request: Request, order_id: str):
        order = _order_or_404(order_id)
        if order.status not in ("preview", "awaiting_payment"):
            return RedirectResponse(f"/order/{order.id}", status_code=303)
        from .pipeline import order_chart

        chart = order_chart(order)
        big = [("Sun", chart.get("Sun")), ("Moon", chart.get("Moon"))]
        if chart.ascendant:
            big.append(("Rising sign", chart.ascendant))
        teasers = []
        for label, p in big:
            where = f" Its house, the {ordinal(p.house)}, points to {HOUSE_THEME[p.house]}." if p.house and label != "Rising sign" else ""
            teasers.append({"label": label, "sign": p.sign, "text": f"{SIGN_STYLE[p.sign].capitalize()}.{where}"})
        bdate = date.fromisoformat(order.birth_date)
        focus_text = " and ".join(FOCUS_LABELS[f].lower() for f in sorted(order.focus_set))
        return page(
            request, "preview.html", order=order, wheel=render_wheel(chart, 600, f"{order.name}'s birth chart"),
            teasers=teasers, chart=chart, focus_text=focus_text, birth_date_text=f"{bdate.day} {bdate:%B %Y}",
            birth_time_text=time_text(time.fromisoformat(order.birth_time)) if order.birth_time else None,
        )

    @app.post("/p/{order_id}/checkout")
    def checkout(order_id: str, email: str = Form("")):
        order = _order_or_404(order_id)
        if order.status not in ("preview", "awaiting_payment"):
            return RedirectResponse(f"/order/{order.id}", status_code=303)
        email = email.strip()[:200] or None
        if not settings.payments_enabled:
            # Pre-order mode: no payment taken yet; we just record interest.
            if not email or "@" not in email:
                raise HTTPException(422, "An email address is needed to reserve a copy.")
            store.update(order.id, status="preorder", email=email)
            return RedirectResponse(f"/order/{order.id}", status_code=303)
        session = stripe_client.v1.checkout.sessions.create(params={
            "mode": "payment",
            "line_items": [{
                "quantity": 1,
                "price_data": {
                    "currency": settings.currency,
                    "unit_amount": settings.price_cents,
                    "product_data": {"name": f"{order.name}'s Birth Sky (personalized PDF book)"},
                },
            }],
            "customer_email": email,
            "client_reference_id": order.id,
            "metadata": {"order_id": order.id},
            "success_url": f"{settings.base_url}/order/{order.id}?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{settings.base_url}/p/{order.id}",
        })
        store.update(order.id, status="awaiting_payment", stripe_session=session.id, email=email)
        return RedirectResponse(session.url, status_code=303)

    def _mark_paid(order_id: str, background: BackgroundTasks) -> None:
        if store.claim(order_id, ("awaiting_payment",), "paid"):
            background.add_task(make_book, store, order_id, writer_client, settings.data_dir)

    @app.get("/order/{order_id}", response_class=HTMLResponse)
    def order_status(request: Request, order_id: str, background: BackgroundTasks, session_id: str | None = None):
        order = _order_or_404(order_id)
        if order.status == "awaiting_payment" and session_id and session_id == order.stripe_session and stripe_client:
            # The webhook usually arrives first; this covers the case where it is slow.
            session = stripe_client.v1.checkout.sessions.retrieve(session_id)
            if session.payment_status == "paid":
                _mark_paid(order.id, background)
                order = store.get(order.id)
        return page(request, "order.html", order=order)

    @app.get("/order/{order_id}/book.pdf")
    def download(order_id: str):
        order = _order_or_404(order_id)
        if order.status != "ready" or not order.pdf_path or not Path(order.pdf_path).exists():
            raise HTTPException(404)
        filename = f"{order.name}-birth-sky.pdf".replace(" ", "-")
        return FileResponse(order.pdf_path, media_type="application/pdf", filename=filename)

    @app.post("/order/{order_id}/delete")
    def delete_order(order_id: str):
        _order_or_404(order_id)
        store.erase(order_id)
        return RedirectResponse("/deleted", status_code=303)

    @app.get("/deleted", response_class=HTMLResponse)
    def deleted(request: Request):
        return page(request, "message.html", title="Your details are deleted",
                    message="We have erased the birth details and the book file for that order.")

    @app.post("/stripe/webhook")
    async def stripe_webhook(request: Request, background: BackgroundTasks):
        if not stripe_client or not settings.stripe_webhook_secret:
            raise HTTPException(404)
        payload = await request.body()
        try:
            event = stripe_client.construct_event(payload, request.headers.get("stripe-signature"), settings.stripe_webhook_secret)
        except Exception:  # noqa: BLE001 - bad signature or payload
            raise HTTPException(400) from None
        if event.type in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
            session = event.data.object
            order_id = (session.metadata or {}).get("order_id")
            if order_id and session.payment_status == "paid":
                _mark_paid(order_id, background)
        return Response(status_code=200)

    @app.get("/sample.pdf")
    def sample_pdf():
        return FileResponse(ROOT / "samples/maya-sample.pdf", media_type="application/pdf", filename="sample-birth-sky-book.pdf")

    @app.get("/policies", response_class=HTMLResponse)
    def policies(request: Request):
        return page(request, "policies.html")

    @app.get("/health")
    def health():
        return {"ok": True, "payments": settings.payments_enabled, "writer": settings.anthropic_configured}

    app.state.store = store
    app.state.settings = settings
    return app


def __getattr__(name: str):
    # `uvicorn chartbook.web.app:app` builds the real app lazily, so importing this module in tests has no side effects.
    if name == "app":
        return create_app()
    raise AttributeError(name)
