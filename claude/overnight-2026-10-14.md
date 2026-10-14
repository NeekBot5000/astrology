# Overnight session, 2026-10-14: report

**Goal (owner's words):** "do whatever means necessary to finish the thing and publish and market it somehow, have full access on computer", plus, mid-session: "add terms of service and all the legal things necessary".
**Time:** started 04:57 UTC. Planned to run to 12:57 UTC (8 hours; no duration was given). Finished early, at about 06:10 UTC, because every task was done and the review pass had nothing left that wasn't invented scope.

## Outcome
- **Published:** a showcase page on claude.ai, private until you share it: https://claude.ai/artifact/VLYVz9jLuJ4ExR9CWAAE6V. It has a free chart wheel in the browser, real sample pages, a sample-book download and a "save as a story image" share button.
- **Legal:** Terms, Privacy, Refunds and withdrawal (with the EU model form), Legal notice, a checkout consent box, and no cookies. All drafts until a lawyer reviews them and your business details are filled in.
- **Marketing:** a ready-to-post content pack, a brand-name shortlist, and search-engine basics.
- **Not possible from here:** putting the real shop on a public address, taking payments, or posting on social media. There are no hosting, Stripe, domain or social accounts in this sandbox, and posting under your name should stay your call.

## Done (with files)
| What | Files | Verified |
|---|---|---|
| Showcase page (published, v3) | `showcase/index.html`, `chart.js`, `wheel.js`, `cities.json`, `pages/` | Browser maths vs. Swiss Ephemeris: 60 random births, worst error 0.31 arcmin, 0/600 retrograde mismatches (`showcase/make_reference.py` + `check_chart.js`); time zones identical to Python on 10 tricky cases; desktop and phone render; share image and sample download exercised with a stand-in |
| Legal pages | `chartbook/web/templates/terms.html`, `privacy.html`, `refunds.html`, `legal_notice.html`, `legal_base.html` | Rendered with and without business details (tests); phone screenshot |
| Checkout consent, recorded | `chartbook/web/app.py`, `store.py` (`consent_at`), `preview.html` | Tests: blocked without the tick, consent stored, sent to Stripe, on the receipt text |
| No cookies | `app.py`, `index.html` (link tag in a hidden field) | Test: no `Set-Cookie` header |
| Legal checklist | `docs/legal/LEGAL_CHECKLIST.md` | Facts written from memory are listed for a lawyer to check |
| Brand shortlist and voice | `docs/BRAND_NAMES.md` | Availability deliberately not claimed |
| Marketing content pack | `docs/MARKETING_CONTENT.md` | – |
| robots.txt, sitemap, product data | `app.py`, `index.html` | Test |
| Owner decisions | `docs/OWNER_DECISIONS.md` | – |
| Review | 10 code-review findings fixed | 61 tests pass, also in a fresh clone following the README literally |

The removed file `chartbook/web/templates/policies.html` (replaced by the four legal pages; `/policies` now redirects to `/terms`) is still in git history.

## Parked (needs you)
- **Taking real orders:** needs hosting, a domain, a Stripe (or Paddle / Lemon Squeezy) account and an Anthropic API key. Steps are in `docs/DEPLOY.md`.
- **Posting the marketing:** needs your social accounts; all copy is ready.
- **Reservation sign-ups on the showcase:** claude.ai pages can only save data for signed-in claude.ai users, so the public can't reserve there. Sign-ups work on the real site.

## Open questions
See `docs/OWNER_DECISIONS.md`. The top three: whether Stripe accepts astrology products, the brand name, and your business and tax setup.

## Suggested next steps
1. Open the showcase page, then share it with 20-30 friends from its Share menu.
2. Work through `docs/OWNER_DECISIONS.md`.
3. Deploy, fill in the `LEGAL_*` settings, place one test order and refund it.
4. Start week 1 of `docs/LAUNCH_PLAN.md`.

---

# Working log
## DONE
[x] Showcase page published as a private Artifact: https://claude.ai/artifact/VLYVz9jLuJ4ExR9CWAAE6V
    Free in-browser chart wheel (showcase/chart.js, wheel.js, cities.json), real sample pages, sample PDF download.
    Verified: browser maths vs Swiss Ephemeris on 60 random charts, max error 0.31 arcmin; 0/600 retrograde mismatches;
    time zones identical to Python on 10 historical/DST cases; desktop + phone render, no horizontal scroll. — ~05:50
    Dropped: Artifact sign-up form (Artifacts only store data for signed-in claude.ai viewers, so the public can't reserve there),
    and therefore the sign-up export script.
[x] Legal pages (owner request): /terms, /privacy, /refunds (incl. EU/UK withdrawal + model form), /legal-notice (Impressum),
    /policies hub; draft banner + [placeholders] until LEGAL_NAME/ADDRESS/COUNTRY set; required checkout consent box
    (terms + immediate delivery + withdrawal acknowledgement), consent time saved on order, sent to Stripe, shown on receipt;
    site now sets NO cookies (link tag moved to hidden form field); AI disclosure + personal-use line in the book;
    docs/legal/LEGAL_CHECKLIST.md (tax, registration, Stripe restricted-business risk, DPAs, licences, facts to verify).
    Verified: 52 tests pass (9 new), phone screenshots of terms + checkout. — ~05:58
[x] docs/BRAND_NAMES.md: 10 screened names (top: Skyprint, Born Beneath, Starwritten), brand voice, checks to run. — ~06:00
[x] docs/MARKETING_CONTENT.md: 10 video scripts, 2 Reddit posts, 10 Pinterest pins, 3 waitlist emails, DMs. — ~06:00
[x] LAUNCH_PLAN/DEPLOY/README point at showcase, content pack, legal steps. — ~06:00
[x] Review: code-review of tonight's work found 10 issues, all fixed (showcase download check, empty-teaser sentence,
    EU-country detection, privacy placeholder, email kept on consent error, link tag kept on "Start again", retrograde
    in check exit code, stale comment, orphan /policies page removed (now redirects to /terms), glyph-drift test).
    Added showcase/make_reference.py. 60 tests pass; JS check passes; showcase republished (v2) with all 9 files. — 06:03
[x] Search basics for the real site: /robots.txt (hides order/admin pages), /sitemap.xml, Product structured data
    (price, PreOrder/InStock), canonical link. Test added. — ~06:10
[x] Showcase v3: "Save as a story image" (1080x1920 PNG with wheel + Sun/Moon/rising + brand line), saved via the
    download capability. Verified locally with a stand-in download API: image renders correctly, no script errors. — ~06:15

## PARKED
