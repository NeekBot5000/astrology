# Project Brief: Personalized Birth-Chart Book (Astrology Gift Product)

## One-line summary
A web product that turns a person's birth date, time and place into a personalized birth-chart reading, delivered as a downloadable PDF "book" (ideal for birthday gifts), with an optional daily-reading subscription added later.

## Where this idea came from
- Found while researching app ideas on Reddit (r/AppIdeas had a popular post about an app that makes a personalized astrology book from your birth chart).
- Ranked #1 for profit potential out of 10 Reddit-sourced ideas. Other ideas were rejected: some are not technically possible (iOS Home Screen organizer), some have no way to charge (inverted-globe sky map), some are already covered by free apps (daily check-in, ADHD task breakdown).

## Market evidence (third-party estimates, not audited)
- Co-Star: about $400K/month, about 30M users. Nebula (top astrology app): about $550K/month. Average astrology-adjacent app: about $125K/month.
- BUT the typical new subscription app is small: median about $492/month; only about 17% of new subscription apps pass $1,000/month recurring revenue.
- Competitors: Co-Star, Nebula, The Pattern, Sanctuary, and Nordastro (launched July 2026 with the exact "personalized book + companion app" idea; 700+ Trustpilot reviews).
- Physical personalized book competitor: The Birthdate Co. sells a hardcover for about $95-$115, written by a team of astrologers. This shows people pay for personalized birthday/gift items.

## Where competitors are weak (our opening)
1. Readings feel generic/cookie-cutter. One Nordastro reviewer said ChatGPT gave a better personalized reading for free.
2. Billing complaints are everywhere in this category: surprise charges, hard-to-cancel subscriptions, free features moving behind paywalls.
3. Advanced chart comparisons are paywalled aggressively (e.g. $14.99/month at one competitor).

## Proposed product (decisions below are proposals, not final)
**Phase 1: One-time personalized PDF book (build this first)**
- Input: name, birth date, exact birth time (allow "unknown"), birth city, and what the person cares about (love, career, growth).
- Calculate the birth chart (see Tech below).
- Generate a multi-chapter personalized reading where every statement is tied to a real placement in that person's chart.
- Output a nicely designed PDF with the chart wheel image, plus a gift option (dedication page / custom gift note).
- Pricing to test: low one-time price for the PDF (suggest testing in the $15-$40 range; the physical book competitor is $95+).
- Clear pricing, no hidden subscription, and a plain refund policy.

**Phase 2 (only if Phase 1 sells): optional daily readings subscription**
- Daily guidance based on today's planet positions vs. the person's chart (called "transits").
- Weekly plans convert best in this category, but billing honesty is our edge: clear terms and one-tap cancel.

## Plain-language glossary
- **Birth chart / natal chart:** a snapshot of where the planets were at the moment someone was born.
- **Ephemeris:** a table/library of planet positions over time. The standard one is the Swiss Ephemeris.
- **Transits:** where the planets are today, compared with a person's birth chart.
- **Synastry:** comparing two people's charts for compatibility.
- **Aspects / houses:** the angles between planets, and the 12 areas of life the chart is divided into.

## Technical approach (suggested)
- Chart math: use an existing library or API, do not write it from scratch. Options: Swiss Ephemeris wrappers (e.g. `pyswisseph` for Python, `swisseph` for Node), or a hosted astrology API. Time zones and birth-location lookup are the trickiest part (handle historical time zones and daylight saving correctly).
- Chart image: render an SVG zodiac wheel from the computed data.
- Writing: use an LLM to write the text, but feed it ONLY the computed chart data (planets, signs, houses, aspects) so each paragraph traces back to real placements. Avoid generic template text.
- PDF: generate from the text + chart SVG (HTML-to-PDF is fine).
- Web first (landing page + order flow). Payments via a standard provider such as Stripe. Do not store payment details.
- Label the product as entertainment and self-reflection.

## Landing page / pre-sale test (do before building everything)
- One-page site with: headline, a sample chapter, price, and a pre-order or buy button.
- Goal: find out if strangers will pay, before investing in the full generator.

## Success and kill criteria
- Realistic expectation (forecast): about 60% chance under $1,000/month after 12 months, about 30% chance $1,000-$10,000/month, about 5-10% chance over $10,000/month. As a one-time gift product the odds are better than a pure subscription app because it's cheaper to test.
- Suggested kill rule: if there are no paid pre-orders after a few weeks of real effort (posting sample content, sharing the landing page), stop or change the angle.

## Risks to keep in mind
- Crowded market with competitors who run paid ads on TikTok/Instagram.
- Free AI alternatives: our readings must be visibly better and more specific.
- Category reputation for sneaky billing: be transparent.
- Refunds/chargebacks on digital products.

## Branding and legal notes
- Use original branding. Do not use competitor names, logos, or copied marketing text (Co-Star, Nebula, Nordastro, The Pattern, Birthdate Co.).
- Do not copy competitor book text or designs; write original content and design.
- Do not store sensitive personal data unnecessarily; birth details are personal, so keep storage minimal and provide delete-on-request.

## Suggested first milestones
1. Birth-chart calculator working from date/time/place (with tests against a few known charts).
2. Chart wheel SVG.
3. Generate one sample chapter from real chart data.
4. Landing page with the sample chapter and a buy/pre-order button.
5. PDF export of a full sample book.
