# Decisions waiting for you

Everything else is built and tested. These are the calls only you can make, roughly in the order they block launch. Each has my recommendation; any of them can be changed later, but the first three are hardest to undo.

| # | Decision | Options | My recommendation | Where it's set |
|---|---|---|---|---|
| 1 | **Is the payment provider OK with astrology?** | Stripe (built in) · Paddle or Lemon Squeezy ("merchant of record": they also collect and pay VAT and sales tax for you) | **Ask Stripe first** (support chat: "personalized astrology PDF books sold as entertainment"). If they say no or it feels risky, switch to Lemon Squeezy or Paddle. That's about a day of coding, which I can do in a later session. | `docs/legal/LEGAL_CHECKLIST.md` item 3 |
| 2 | **Brand name** | Decided: **Skyprint** | Still do the domain, trademark and handle checks before buying anything; if it's taken, "Born Beneath" is next. | `BRAND` in `chartbook/book.py`, plus `showcase/index.html` |
| 3 | **Business details and tax** | Sole trader vs. company; VAT registration or small-business exemption | **Start as a sole trader** if your country allows it, and book one session with a tax adviser about VAT on digital goods. A merchant-of-record provider (decision 1) removes most of the tax work. | `LEGAL_*` and `VAT_ID` settings |
| 4 | **Swiss Ephemeris licence** | Free (AGPL: publish the site's code) · Paid professional licence (about CHF 750, check current price) | **Publish the code.** The value is in the writing and marketing, not the code. Make the GitHub repo public, or add a "source code" link in the footer. | `docs/FORECAST.md` |
| 5 | **Price** | Decided: **$9** (was $29) | If many previews buy quickly, test $15 for two weeks; if very few buy, the price isn't the problem, so look at the page and the traffic first. | `PRICE_CENTS` |
| 6 | **Refund promise** | Keep the 14-day no-questions refund · legal minimum only | **Keep it.** It's the honest-pricing story, and digital refunds cost little. | Terms, refunds page, landing page |
| 7 | **Hosting** | Render · Railway · Fly.io | **Render**: simplest steps in `docs/DEPLOY.md`, about $7-15/month with a disk. | `docs/DEPLOY.md` |
| 8 | **Read books before release?** | Review mode on or off | **On for the first ~10 orders** (`REVIEW_BOOKS=true`), then off once you trust the writing. | `REVIEW_BOOKS` |
| 9 | **Who sees the showcase page** | Keep private · share with friends · public link | **Share with 20-30 friends now** (its Share menu) for honest feedback, as in week 1 of the launch plan. It can't take orders, so don't put it in public posts; use the real site for that. | claude.ai page's Share menu |
| 10 | **Lawyer review of the legal pages** | Lawyer · legal-text service · none | **One fixed-fee review** before real orders, focused on the facts listed at the end of the legal checklist. | `docs/legal/LEGAL_CHECKLIST.md` |

## What happens after you decide
1. Tell a new session the answers (or set them yourself). The code needs only settings for 3, 5, 7 and 8; 2 is a one-line change plus regenerating images; 1 may need a payment-provider switch.
2. Deploy (`docs/DEPLOY.md`), place one real test order, refund it.
3. Run `scripts/check_writer.py` with your API key and read the three test chapters.
4. Start week 1 of `docs/LAUNCH_PLAN.md`, using the copy in `docs/MARKETING_CONTENT.md`.
