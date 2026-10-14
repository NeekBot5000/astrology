# Progress log

Newest entries go at the top. Each entry: date, what was done, what was verified, what is next.

## 2026-10-14: Milestones 2-5 done, website and launch plan ready
**Built**
- Chart wheel image (`wheel.py`), drawn with original line glyphs so it looks the same everywhere.
- AI writer (`reading.py`): Claude writes 7 chapters from the chart facts only. Every paragraph must list the facts it uses; the code rejects unknown or missing citations, banned clichés and badly sized paragraphs, and asks for one rewrite. Instructions and facts are cached, so a whole book costs roughly $0.30-0.80.
- PDF book (`book.py`): 6x9 in, cover with the person's own wheel, gift dedication, chart page with positions table, a reading guide, 7 chapters, and a ✦ line under every paragraph naming the placements it's based on.
- Sample book for a made-up person, "Maya" (`samples/maya.json` + `maya-sample.pdf`, 22 pages). I wrote it by hand in the same format and it passes the same automatic checks.
- Website (`chartbook/web/`): landing page with the sample chapter, free chart preview, Stripe checkout, an order page that shows progress, PDF download, one-click "erase my data", automatic deletion after 30 days, a private stats page with visitors → previews → paid per marketing link, and a CSV of reserved-copy emails. Without a Stripe key it runs in "reserve a copy" mode (collects emails, takes no money), which suits the pre-sale test.
- `make_book` command, Dockerfile, `docs/DEPLOY.md`, `docs/LAUNCH_PLAN.md`.
- Optional review mode (`REVIEW_BOOKS=true`): you read and approve each book at `/admin/review` before the customer gets it, with a "rewrite" button. Failed books show on the stats page with a retry button.
- Stripe receipts include the link to the customer's download page, so a closed tab doesn't lose the book (the site sends no email of its own yet).
- AI cost is recorded per book and averaged on the stats page.
- Books interrupted by a restart or deploy resume automatically when the server starts.
- Marketing images in `marketing/` (3 Pinterest pins, 2 Instagram posts, link preview card), made from the sample book by `scripts/make_marketing_images.py`.
- `scripts/check_writer.py`: once you have an API key, writes 3 test chapters for tricky charts (about $0.25) so you can check quality before launch.

**Verified**
- 44 automated tests pass (the PDF test needs Chromium): chart accuracy, writer validation and retry using a fake AI, the full paid flow using a fake Stripe (payment → writing → download → delete), webhook signature check, no double writing, purge rules, link tracking.
- Accessibility: automated axe-core scan clean on all pages; contrast fixed (input borders, focus ring, wheel labels); keyboard order checked; no sideways scrolling at 320 px or 200% text.
- A security review of the whole branch found no high-confidence issues. A code review found 10 bugs (e.g. a reservation could be erased mid-checkout, paid sales vanished from stats after deletion, rate limit broken behind a hosting proxy); all fixed with tests.

**NOT verified (needs the owner's accounts or a normal network)**
- A real Claude-written book: no API key in the build sandbox. The writer is tested with a fake.
- Real Stripe payments: tested with a fake Stripe client only.
- Place lookup by name (OpenStreetMap), because the sandbox blocks it.
- Building the Docker image: no Docker engine in the sandbox. `requirements.txt` installs and the app starts in a fresh environment.

**Decisions for the owner** (I picked placeholders; change any of them)
1. Brand name: placeholder "Birth Sky Books". Check trademark, domain and social handles.
2. Price: $29 placeholder (`PRICE_CENTS`).
3. Refund policy: 14-day no-questions refund is promised on the site. Keep it?
4. Swiss Ephemeris license (AGPL) vs. buying the professional license, before taking real money.
5. Hosting provider, support email, Stripe and Anthropic accounts.

**Next**: owner decisions above → deploy → place one real test order → start the launch plan.

## 2026-10-13: Milestone 1 done (birth-chart calculator) + founder forecast
- Built `chartbook/`, a Python birth-chart calculator using the Swiss Ephemeris (the standard planet-position library). From a birth date, time and place it works out the sign and degree of the Sun, Moon, planets and North Node, retrograde motion (when a planet appears to move backwards), the 12 houses (Placidus, switching to whole-sign near the poles), the Ascendant and Midheaven, and the major aspects (angles between planets).
- Handles historical time zones and daylight saving, refuses birth times that didn't exist or happened twice when clocks changed, and supports an unknown birth time (houses are left out, with a note).
- Verified with 10 automated tests (`pytest`), all passing. Einstein's chart matches the published reference values to the arcminute, and the Sun sits at exactly 0° Aries / 0° Cancer at the 2024 equinox and the 2025 solstice.
- NOT verified: looking up places by name (OpenStreetMap). The build sandbox blocks that network call. Entering latitude and longitude directly works.
- Wrote `docs/FORECAST.md`, the founder-style forecast. New risk found: the Swiss Ephemeris license (AGPL) means either publishing the site's code or buying a professional license. The owner has to decide.
- Next: milestone 2, the chart wheel SVG image.

## 2026-10-13: Repo created
- Created the repository with the project brief, instructions for Claude Code, and this log.
- Nothing is built yet.
- Next: milestone 1, a birth-chart calculator that works from date, time and place, with tests against a few known charts.
