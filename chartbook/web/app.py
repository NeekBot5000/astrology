"""The website: landing page, free chart preview, checkout and delivery.

Run locally:  uvicorn chartbook.web.app:app --reload
"""

from __future__ import annotations

import base64
import binascii
import csv
import hmac
import io
import logging
from html import escape as html_escape
import re
import threading
import time as _time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
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
from .store import Store, now

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
BOT_UA = re.compile(r"bot[/;)\-]|bot$|crawl|spider|slurp|facebookexternalhit|curl/|python-requests|headless", re.I)
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


def clean_tag(value: str | None) -> str:
    """Normalize a marketing link tag: lowercase letters, digits and dashes, at most 30 characters."""
    return re.sub(r"[^a-z0-9-]", "", (value or "").lower())[:30]


EU_COUNTRIES = {
    "austria", "belgium", "bulgaria", "croatia", "cyprus", "czechia", "czech republic", "denmark", "estonia", "finland",
    "france", "germany", "greece", "hungary", "ireland", "italy", "latvia", "lithuania", "luxembourg", "malta",
    "netherlands", "poland", "portugal", "romania", "slovakia", "slovenia", "spain", "sweden",
    # common local names and codes
    "deutschland", "österreich", "osterreich", "nederland", "france", "españa", "espana", "italia", "polska", "sverige",
    "danmark", "suomi", "belgië", "belgique", "éire", "eire", "at", "de", "nl", "fr", "es", "it", "be", "ie", "eu",
}


def is_eu_country(name: str | None) -> bool:
    key = re.sub(r"^the\s+", "", (name or "").strip().lower())
    return key in EU_COUNTRIES


def legal_context(settings: Settings) -> dict:
    """Business details for the legal pages, with visible [placeholders] for anything not configured."""
    address = settings.legal_address or "[Street and number, postcode, city, country]"
    return {
        "ready": settings.legal_ready,
        "name": settings.legal_name or "[Your full legal name or registered company name]",
        "address": address,
        "address_html": "<br>".join(html_escape(part.strip()) for part in address.split(",")),
        "country": settings.legal_country or "[country]",
        "country_set": bool(settings.legal_country),
        "vat_id": settings.vat_id,
        "effective": settings.legal_effective_date,
        "eu": is_eu_country(settings.legal_country),
    }


def _anthropic_client():
    import anthropic

    return anthropic.Anthropic()


def create_app(settings: Settings | None = None, geocode=lookup_place, writer_client=_anthropic_client, stripe_client=None) -> FastAPI:
    settings = settings or load_settings()
    store = Store(settings.data_dir / "orders.sqlite3")
    if stripe_client is None and settings.payments_enabled:
        import stripe

        stripe_client = stripe.StripeClient(settings.stripe_secret_key)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        # Restart books that were interrupted, e.g. by a deploy or crash while writing.
        stuck = store.with_status("writing") + store.with_status("paid")
        for order in stuck:
            store.update(order.id, status="paid")
            threading.Thread(
                target=make_book, args=(store, order.id, writer_client, settings.data_dir, settings.review_books), daemon=True
            ).start()
        if stuck:
            log.warning("Resumed %d unfinished book(s)", len(stuck))
        yield

    app = FastAPI(title=BRAND, docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
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

    landing = dict(chapter=sample_chapter, sample_sources=sample_sources, hero_wheel=hero_wheel, focus_labels=FOCUS_LABELS,
                   price_number=f"{settings.price_cents / 100:.2f}", currency=settings.currency)

    legal = legal_context(settings)

    def page(request: Request, name: str, status_code: int = 200, **ctx) -> HTMLResponse:
        ctx.update(brand=BRAND, price=settings.price_text, payments=settings.payments_enabled,
                   support_email=settings.support_email, keep_days=settings.keep_days, base_url=settings.base_url,
                   legal=legal)
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
    def index(request: Request, src: str = ""):
        tag = clean_tag(src)
        if not BOT_UA.search(request.headers.get("user-agent", "")):
            store.count_visit(tag or "direct")
        # The link tag travels in a hidden form field rather than a cookie, so the site sets no cookies at all
        # and needs no cookie banner.
        return page(request, "index.html", form={"src": tag}, errors=[], **landing)

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
        src: str = Form(""),
    ):
        form = dict(name=name, birth_date=birth_date, birth_time=birth_time, time_unknown=time_unknown,
                    place=place, focus=focus, dedication=dedication, src=clean_tag(src))
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
            source=clean_tag(src) or None,
        )
        return RedirectResponse(f"/p/{order.id}", status_code=303)

    def buyable_statuses() -> tuple[str, ...]:
        # People who reserved a copy can buy from their link once payments are switched on.
        return ("preview", "awaiting_payment", "preorder") if settings.payments_enabled else ("preview", "awaiting_payment")

    def _order_or_404(order_id: str):
        order = store.get(order_id)
        if not order or order.status == "deleted":
            raise HTTPException(404)
        return order

    @app.get("/p/{order_id}", response_class=HTMLResponse)
    def show_preview(request: Request, order_id: str):
        return render_preview(request, order_id)

    def render_preview(request: Request, order_id: str, error: str | None = None, status_code: int = 200,
                       email: str | None = None):
        order = _order_or_404(order_id)
        if order.status not in buyable_statuses():
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
            request, "preview.html", status_code=status_code, error=error, order=order, email=email or order.email or "", wheel=render_wheel(chart, 600, f"{order.name}'s birth chart"),
            teasers=teasers, chart=chart, focus_text=focus_text, birth_date_text=f"{bdate.day} {bdate:%B %Y}",
            birth_time_text=time_text(time.fromisoformat(order.birth_time)) if order.birth_time else None,
        )

    @app.post("/p/{order_id}/checkout")
    def checkout(request: Request, order_id: str, email: str = Form(""), agree: bool = Form(False)):
        order = _order_or_404(order_id)
        if order.status not in buyable_statuses():
            return RedirectResponse(f"/order/{order.id}", status_code=303)
        email = email.strip()[:200] or order.email  # keep the reservation email if the field is left blank
        if settings.payments_enabled and not agree:
            # EU/UK law: for instant digital delivery the buyer must agree to immediate supply and acknowledge
            # that the withdrawal right ends on delivery. We also need acceptance of the terms.
            return render_preview(request, order_id, error="Please tick the box to agree to the terms before paying.",
                                  status_code=422, email=email)
        if not settings.payments_enabled:
            # Pre-order mode: no payment taken yet; we just record interest.
            if not email or "@" not in email:
                raise HTTPException(422, "An email address is needed to reserve a copy.")
            store.update(order.id, status="preorder", email=email, reserved_at=order.reserved_at or now().isoformat())
            return RedirectResponse(f"/order/{order.id}", status_code=303)
        consent_at = now().isoformat()
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
            # Shown on Stripe's emailed receipt, so the customer can always find the download page again.
            # The second sentence confirms the customer's withdrawal consent on a durable medium (the receipt).
            "payment_intent_data": {"description": (
                f"Your book: {settings.base_url}/order/{order.id} . You agreed to the terms and asked us to make "
                "the book immediately; your EU/UK right of withdrawal ends once it is available to download. "
                "Our 14-day refund promise still applies.")},
            "metadata": {"order_id": order.id, "terms_accepted_at": consent_at},
            "success_url": f"{settings.base_url}/order/{order.id}?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{settings.base_url}/p/{order.id}",
        })
        store.update(order.id, status="awaiting_payment", stripe_session=session.id, email=email,
                     checkout_at=now().isoformat(), consent_at=consent_at)
        return RedirectResponse(session.url, status_code=303)

    def _mark_paid(order_id: str, background: BackgroundTasks) -> None:
        if store.claim(order_id, ("awaiting_payment",), "paid"):
            store.update(order_id, paid_at=now().isoformat())
            background.add_task(make_book, store, order_id, writer_client, settings.data_dir, settings.review_books)

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
        safe_name = re.sub(r"[^A-Za-z0-9-]+", "-", order.name).strip("-") or "your"
        filename = f"{safe_name}-birth-sky.pdf"
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

    @app.get("/policies")
    def policies():
        return RedirectResponse("/terms", status_code=301)  # old address, kept so earlier links still work

    @app.get("/terms", response_class=HTMLResponse)
    def terms(request: Request):
        return page(request, "terms.html", legal_title="Terms of service", active="terms")

    @app.get("/privacy", response_class=HTMLResponse)
    def privacy(request: Request):
        return page(request, "privacy.html", legal_title="Privacy policy", active="privacy")

    @app.get("/refunds", response_class=HTMLResponse)
    def refunds(request: Request):
        return page(request, "refunds.html", legal_title="Refunds and right of withdrawal", active="refunds")

    @app.get("/legal-notice", response_class=HTMLResponse)
    def legal_notice(request: Request):
        return page(request, "legal_notice.html", legal_title="Legal notice", active="notice")

    def require_admin(request: Request) -> None:
        """Owner-only pages use the browser's password prompt (any username, password = ADMIN_TOKEN).

        Disabled entirely when ADMIN_TOKEN is unset. Using a header instead of ?token= keeps the
        password out of server logs and browser history.
        """
        if not settings.admin_token:
            raise HTTPException(404)
        given = ""
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("basic "):
            try:
                given = base64.b64decode(auth[6:]).decode("utf-8").partition(":")[2]
            except (ValueError, binascii.Error):
                given = ""
        if not hmac.compare_digest(given.encode(), settings.admin_token.encode()):
            raise HTTPException(401, headers={"WWW-Authenticate": 'Basic realm="owner"'})

    @app.get("/admin/stats", response_class=HTMLResponse)
    def stats(request: Request, since: str = ""):
        """Pre-sale test numbers for the owner."""
        require_admin(request)
        funnel = store.funnel(since or None)
        # Erased rows keep their reserved/paid timestamps, so these totals don't shrink over time.
        previews = sum(r["previews"] for r in funnel)
        reached = {"preorder": sum(r["preorders"] for r in funnel), "paid": store.paid_count(since or None)}
        counts = store.counts(since or None)
        avg = store.average_cost_cents()
        return page(request, "stats.html", counts=counts, previews=previews, reached=reached, since=since, funnel=funnel,
                    avg_cost=None if avg is None else avg / 100, failed=store.with_status("failed"))

    @app.get("/admin/preorders.csv")
    def preorders_csv(request: Request):
        """Emails of people who reserved a copy, so the owner can tell them when ordering opens."""
        require_admin(request)
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(["reserved_at", "email", "name", "order_link", "link_tag"])
        for o in store.preorders():
            w.writerow([o.created_at[:10], o.email, o.name, f"{settings.base_url}/p/{o.id}", o.source or ""])
        return Response(out.getvalue(), media_type="text/csv",
                        headers={"Content-Disposition": 'attachment; filename="preorders.csv"'})

    @app.get("/admin/review", response_class=HTMLResponse)
    def review_list(request: Request):
        require_admin(request)
        return page(request, "review.html", orders=store.with_status("review"), review_on=settings.review_books)

    @app.get("/admin/review/{order_id}.pdf")
    def review_pdf(request: Request, order_id: str):
        require_admin(request)
        order = _order_or_404(order_id)
        if order.status != "review" or not order.pdf_path:
            raise HTTPException(404)
        return FileResponse(order.pdf_path, media_type="application/pdf")

    @app.post("/admin/review/{order_id}/approve")
    def review_approve(request: Request, order_id: str):
        require_admin(request)
        if store.claim(order_id, ("review",), "ready"):
            store.update(order_id, ready_at=now().isoformat())
        return RedirectResponse("/admin/review", status_code=303)

    @app.post("/admin/review/{order_id}/rewrite")
    def review_rewrite(request: Request, order_id: str, background: BackgroundTasks):
        require_admin(request)
        if store.claim(order_id, ("review", "failed"), "paid"):
            background.add_task(make_book, store, order_id, writer_client, settings.data_dir, settings.review_books)
        return RedirectResponse("/admin/review", status_code=303)

    @app.get("/robots.txt")
    def robots():
        # Keep private order pages and owner pages out of search engines.
        body = (
            "User-agent: *\nDisallow: /p/\nDisallow: /order/\nDisallow: /admin/\n"
            f"Sitemap: {settings.base_url}/sitemap.xml\n"
        )
        return Response(body, media_type="text/plain")

    @app.get("/sitemap.xml")
    def sitemap():
        paths = ["/", "/terms", "/privacy", "/refunds", "/legal-notice"]
        urls = "".join(f"<url><loc>{settings.base_url}{p}</loc></url>" for p in paths)
        body = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
        return Response(body, media_type="application/xml")

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
