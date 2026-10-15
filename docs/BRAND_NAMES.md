# Brand name shortlist

"Skyprint" is a placeholder. The name is hard to change once a domain, social accounts and reviews are attached to it, so take a few days over it. **I can't check whether any of these names is free.** Every name below is *unverified* until you check it yourself (steps at the end), and the trademark with a lawyer.

## What the name has to do
- **Say "gift" and "personal", not "app".** Buyers are mostly people buying for someone else.
- **Be easy to say and spell after hearing it once** in a video voice-over or a friend's recommendation.
- **Fit the existing look:** midnight blue, soft gold, a classic book serif. Bookish beats techy.
- **Lean distinctive, not purely descriptive.** "Astrology Birth Chart Book" is clear but can't be trademarked or remembered. A half-descriptive name is the sweet spot.
- **Hard nos:** anything close to Co-Star, Nebula, Nordastro, The Pattern, Sanctuary or Birthdate Co.; no zodiac puns that sound like a horoscope app; nothing that implies prediction ("Fortune", "Destiny").
- **Must work in English and German** (your likely home market).

## Shortlist

| Name | Style | Sayable / spellable | Memorable | Meaning and connotations (EN / DE) | Notes |
|---|---|---|---|---|---|
| **Skyprint** | Coined compound | Yes / yes | High | "The print the sky left on you", like a fingerprint. Neutral in German. | My top pick: short, ownable, works as "your Skyprint book". Check for printing companies with the same name. |
| **Born Beneath** | Real-word phrase | Yes / yes | High | "Born beneath these stars." Warm and gift-like. "Beneath" may be unfamiliar to some German speakers. | Lovely on a cover ("Maya, born beneath…"). Two words make the domain longer. |
| **Starwritten** | Compound | Yes / mostly ("star-written"?) | Medium-high | "Written in the stars", and the book is literally written from the stars. | Likely used by others (books, songs); check carefully. |
| **Sky Ledger** | Suggestive | Yes / yes | Medium | A ledger is a record: matches "every paragraph shows its receipts". "Ledger" also suggests finance and crypto wallets. | Clever, but the finance association works against a gift. |
| **First Sky** | Real-word | Yes / yes | Medium | The first sky you ever saw. Simple, emotional. | Generic words, so trademarking may be harder. |
| **Ascendant Press** | Suggestive | Yes / yes | Medium | An astrology term plus "press" (publisher), so it sounds like a real book publisher. | Astrology fans love the term; others may not know it. |
| **Natal Notes** | Descriptive, alliterative | Yes / yes | Medium | "Natal" (birth) chart, "notes". In German "Natal" also means the Brazilian city and the South African province. | Clear to astrology fans, jargon to gift-buyers. |
| **Zenith & Page** | Compound ("& Co" style) | Yes / yes | Medium | "Zenith" (highest point of the sky) plus "page". Feels like a stationery brand. | Ampersand names are awkward in domains and handles. |
| **Your Sky Book** | Descriptive | Yes / yes | Low-medium | Says exactly what it is. | Very hard to protect as a trademark; fine as a tagline. |
| **Skyprint** | Descriptive (current) | Yes / yes | Medium | Clear and already on every page. | Safe fallback if nothing else clears the checks. |

**Recommendation:** check **Skyprint** first, then **Born Beneath**, then **Starwritten**. Keep "Skyprint" as the fallback. Whichever wins, "A birth-chart book written for one person" stays the tagline.

## Brand voice
The brand sounds like a well-read friend who happens to know astrology: warm, specific and honest, never mystical or salesy. It talks to gift-givers as thoughtful people with little time, and to astrology fans as people who know the difference between a real chart and a horoscope column. Every piece of writing should leave the reader feeling *seen* and *not tricked*: the book is about someone real, and the price is exactly what it says.

| Do | Don't |
|---|---|
| Name the real thing: "your Moon in Leo, 2nd house", "one payment of $8". | Use vague mysticism: "the universe is guiding you", "cosmic energy". |
| Say it plainly and kindly, including the tensions in a chart. | Flatter everyone or promise outcomes: no predictions about love, money or health. |
| Be honest about how it works (calculated sky, written by AI, checked automatically). | Use urgency tricks or hype: "only 3 left!", "limited time", fake countdowns. |

## Before you commit: checks only you can run
1. **Domain:** search the `.com` (and your country's ending, e.g. `.de`) at any registrar (Namecheap, Porkbun, IONOS).
2. **Trademark:** search the name for "class 16" (printed matter) and "class 41/45" (publishing / personal services) in the **EUIPO** database (EU), **DPMA** (Germany) and **USPTO** (US), then have a lawyer confirm before you spend money on branding.
3. **Social handles:** check TikTok, Instagram and Pinterest, the three launch channels.
4. **Web search:** search the name plus "astrology" and plus "book" to spot anyone already using it in this space.
5. **Say it out loud** to three friends and ask them to type it. If two get it wrong, drop it.

Once chosen, change the brand in `BRAND` in `chartbook/book.py` (the website and books follow) and in the text of `showcase/index.html`, then re-run `scripts/make_marketing_images.py`, rebuild the sample book (`python -m chartbook.make_book --from-json samples/maya.json --out samples/maya-sample.pdf`) and republish the showcase page.
