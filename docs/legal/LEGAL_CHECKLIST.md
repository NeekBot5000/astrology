# Legal checklist before taking real orders

The website now has draft **Terms of Service**, a **Privacy Policy**, a **Refunds and right of withdrawal** page with the EU model withdrawal form, and a **Legal notice** (the German "Impressum"). They are written in plain language for this exact product, but **they are drafts, not legal advice**. Laws differ by country, and I can't know yours for sure. Plan for one paid review by a lawyer (often a fixed fee for small online shops), or use a reputable legal-text service for your country.

Where the pages live: `chartbook/web/templates/terms.html`, `privacy.html`, `refunds.html`, `legal_notice.html` (shown at `/terms`, `/privacy`, `/refunds`, `/legal-notice`).

## 1. Fill in your business details (needed before launch)
Set these settings (environment variables, see `.env.example`). Until the first three are set, every legal page shows a visible "Draft" banner and [placeholders]:

| Setting | What to put | Example |
|---|---|---|
| `LEGAL_NAME` | Your full name, or your registered company name | `Sam Example` or `Example UG (haftungsbeschränkt)` |
| `LEGAL_ADDRESS` | A postal address where you can receive letters (commas between lines) | `Musterstrasse 1, 10115 Berlin, Germany` |
| `LEGAL_COUNTRY` | Country whose law governs the terms | `Germany` |
| `VAT_ID` | Your VAT or sales-tax number, if you have one | `DE123456789` |
| `LEGAL_EFFECTIVE_DATE` | The day the terms take effect | `2026-11-02` |

Then search the pages for remaining `[square brackets]`: your hosting provider's name in the privacy policy, a phone number in the legal notice if your country requires one, and an EU representative if you're based outside the EU but sell to EU customers.

## 2. Things the pages can't do for you

| # | Item | Why it matters | Plain-language next step |
|---|---|---|---|
| 1 | **Register the business** | Selling regularly for profit usually counts as a business. In Germany, for example, that means a trade registration (Gewerbeanmeldung) and telling the tax office. | Check your local rules; a sole-trader registration is usually cheap and quick. |
| 2 | **Sales tax / VAT on digital products** | Digital goods sold to consumers are often taxed at the *buyer's* country rate (EU, UK, and many US states). Small-business exemptions exist in some countries (for example Germany's Kleinunternehmer rule) but have conditions. | Ask a tax adviser. Stripe Tax can calculate and collect it automatically (small extra fee). Then set the price text to "incl. VAT" where required. |
| 3 | **Stripe allows the business** | Payment providers keep lists of restricted businesses. Astrology and "psychic" services sometimes appear on them, so this is a real risk. | **Before building more**, read Stripe's restricted-business list or ask Stripe support whether "personalized astrology PDF books, sold as entertainment" is accepted. If not, alternatives include Paddle or Lemon Squeezy (they also handle VAT for you as the seller of record). |
| 4 | **Swiss Ephemeris licence** | The free licence (AGPL) requires publishing the website's source code. The alternative is Astrodienst's paid professional licence. | Pick one. Publishing the code is fine for this business. |
| 5 | **Data processing agreements (DPAs)** | GDPR requires a contract with each service that handles customer data for you. | Accept the standard DPAs of Stripe, Anthropic and your hosting provider in their dashboards (usually one click). |
| 6 | **Anthropic's terms** | Using the API commercially means following Anthropic's commercial terms and usage policy. The privacy policy says API data isn't used for training; confirm that's still true for your account. | Read the commercial terms when creating the API account. |
| 7 | **Attribution for free components** | Several free components require credit. | Already done: Swiss Ephemeris, OpenStreetMap, fonts (legal notice and book); GeoNames and Astronomy Engine (showcase page). Keep them if you redesign. |
| 8 | **Trademark check on the brand name** | "Birth Sky Books" is a placeholder; using a name someone else has registered can force a costly rename. | Search your country's trademark register (e.g. DPMA, EUIPO, USPTO) before buying the domain. |
| 9 | **Marketing rules** | Paid or gifted creator posts must be labelled as ads. You can only email people who agreed to it. | Ask creators to tag posts #ad. Only email reservation sign-ups about the launch they signed up for. |
| 10 | **Records** | Tax law usually requires keeping invoices and order records for years (often up to 10). The site already keeps order records but deletes birth details. | Export Stripe reports yearly; keep them with your accounts. |
| 11 | **Accessibility law** | The EU's European Accessibility Act covers online shops, but very small businesses (under 10 staff and under €2M turnover) are exempt for services. The site already passed an automated accessibility check. | Nothing needed now; revisit if the business grows. |

## 3. How the website already supports the law
- **Withdrawal consent (EU/UK):** buyers must tick a box agreeing to the terms, asking for immediate delivery and acknowledging that the withdrawal right ends at download. The time is saved on the order (`consent_at`), sent to Stripe as `terms_accepted_at`, and confirmed on the Stripe receipt.
- **No cookies:** the site sets no cookies (the marketing link tag now travels in a hidden form field), so no cookie banner is needed. Stripe's own checkout page handles its own cookies.
- **Data minimization and deletion:** previews deleted after 2 days, reservations after 120 days, books and birth details after 30 days; one-click erase for customers.
- **Clear pricing:** one price, charged once, no subscription; a 14-day refund promise on top of legal rights.
- **AI disclosure:** the FAQ, terms, privacy policy and the book itself say the text is written by AI from the calculated chart.

## 4. Facts in the drafts that came from memory (lawyer: please check)
- The name of the German Impressum law (§ 5 DDG, which replaced § 5 TMG in 2024).
- EU withdrawal-right rules for digital content (immediate-supply consent plus acknowledgement) and the model withdrawal form wording, adapted from the EU Consumer Rights Directive.
- That small German traders aren't required to join consumer arbitration, and the wording of that statement.
- That data sent through Anthropic's commercial API isn't used for model training.
- The EU-US Data Privacy Framework and standard contractual clauses as the transfer mechanisms for US providers.
- Server-log retention of 14 days, which depends on your hosting provider's settings.
