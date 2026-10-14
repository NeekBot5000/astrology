# Launch plan: "The Christmas pre-sale test"

> **Start here (added 14 Oct):** before the shop is online you can already share the **showcase page**, a private claude.ai page with a free chart-wheel tool, real sample pages and a sample download: https://claude.ai/artifact/VLYVz9jLuJ4ExR9CWAAE6V. Open its Share menu to choose who can see it. Use it for the "friends" step and early feedback. It can't take orders or sign-ups; that needs the real site (`docs/DEPLOY.md`). Ready-to-post copy is in `docs/MARKETING_CONTENT.md`.

**Goal:** find out, cheaply and fast, whether strangers will pay $9 for a personalized birth-chart book.
**Kill rule:** after ~1,000 targeted visitors, fewer than 5 paid orders means stop or change the angle (see `FORECAST.md`).
**Budget:** close to $0 in ads. The cost is your time: about 5-7 hours a week for 7 weeks.
**Window:** 2 Nov to 24 Dec 2026. Christmas helps us: a PDF gift that arrives within minutes is the perfect last-minute present.

Every number below can be read from the site's stats page (`/admin/stats`, password = your `ADMIN_TOKEN`). Each channel gets its own link tag (`?src=tiktok` etc.), so you can see which channel sends visitors who actually buy.

---

## 1. Who we're selling to

**Main buyer: the gift-giver.** Mostly women aged 22-40 buying for a best friend, sister, partner or mum. They know a little astrology (their "big three": Sun, Moon and rising sign) and want a present that feels personal and isn't another candle. They're short on time and wary of subscriptions.

**Second buyer: the self-buyer.** Someone into astrology who is tired of the generic text in the apps and wants something deeper about their own chart.

**Where they spend time:** TikTok and Instagram Reels (astrology content is huge there), Pinterest (gift ideas, "aesthetic" astrology), Reddit (gift and astrology communities, which are very strict about promotion), group chats (word of mouth).

**What stops them buying:** "Is this just ChatGPT?", "Will I get trapped in a subscription?", "Is it worth $9 when apps are free?"

## 2. What we say

**Core message:** *A birth-chart book written for one person, where every page shows which part of their chart it comes from.*

| Message | Proof we can show |
|---|---|
| It's actually about **them**, not their Sun sign | The ✦ source line under every paragraph; the free preview shows their real chart wheel |
| A gift that feels thoughtful, made in minutes | Dedication page with your own words; instant PDF; prints like a paperback |
| Pay once. Seriously. | No account, no subscription, 14-day refund. Say it plainly, because competitors' reviews are full of billing complaints |
| See it before you buy | Free chart preview + Maya's full 22-page sample book |

**Tone by channel:** TikTok and Reels: playful and specific ("POV: your friend's birth chart roasts her gently"). Pinterest: gift-guide calm. Reddit: honest maker story, no hype.

## 3. Channels

| Channel | Why | Format | Effort | Link tag |
|---|---|---|---|---|
| **TikTok + Instagram Reels** (main bet) | Where astrology audiences and gift browsers are; one hit can bring thousands of visitors for free | 20-40 s videos showing a real book page, chart reveals, "gift idea" | High | `tiktok`, `reels` |
| **Pinterest** | People plan gifts there weeks ahead; pins keep bringing visitors for months | Gift-guide pins with the book cover and sample pages | Medium | `pinterest` |
| **Reddit** | High-intent, honest feedback. One good maker story can carry a launch | Value-first posts in communities that allow them (see rules below) | Medium | `reddit` |
| **Friends and group chats** | The first 5 sales usually come from people one step away from you | Personal message with the sample book | Low | `friends` |
| **Small astrology creators** (week 4+, only if videos work) | Borrow trust | Free book for them + a discount code for followers | Medium | `creator-<name>` |

**Reddit rules matter.** Most astrology subreddits ban self-promotion. Breaking that gets the account banned and the brand remembered badly. Only post where promotion is allowed (r/SideProject, r/AppIdeas, the weekly "self-promo" threads some communities run), and lead with something useful. The best angle: **"I built the idea from a popular r/AppIdeas post. Here's what I learned"**, since that's literally where this idea came from.

Paid ads: **none** during the test. If the test passes, a $100-200 TikTok Spark Ads experiment on the best organic video is the next step.

## 4. Calendar

| Week | What to make and post | Channel | Notes |
|---|---|---|---|
| Before launch (19 Oct-1 Nov) | Deploy the site, buy the domain, connect Stripe (live mode), add the Anthropic key, place one real test order and refund it | Site | **Must be done before anything else**: checkout must work |
| | Make 6 videos in one session (scripts below); make 10 pins | TikTok, Pinterest | Batch production saves hours |
| 1 (2-8 Nov) | Personal message to 20-30 friends with the sample book | Friends | Ask for honest feedback, not favours |
| | Post 3 videos (#1, #2, #3) | TikTok + Reels | Post the same video to both |
| | Publish 10 pins | Pinterest | |
| 2 (9-15 Nov) | r/AppIdeas follow-up post (maker story) | Reddit | Answer every comment within the day |
| | 3 videos: repeat the best one with a new hook + #4, #5 | TikTok + Reels | |
| 3 (16-22 Nov) | r/SideProject post with what week 1-2 taught you | Reddit | |
| | 3 videos, including one "reading a stranger's chart in the comments" | TikTok + Reels | Comment replies are cheap, fast content |
| 4 (23-29 Nov) | "Black Friday: no discount, just no subscription" video (honest-pricing angle) | TikTok + Reels | Black Friday is 27 Nov |
| | **Checkpoint 1**: read the stats page. Fewer than 300 visitors? Double video output and try 3 new hooks | | |
| 5 (30 Nov-6 Dec) | Gift-guide push: "gift for the friend who has everything" | All | |
| | Contact 5-10 small astrology creators (offer a free book) | Creators | Only if some videos passed ~2,000 views |
| 6 (7-13 Dec) | "Last-minute gift that arrives in minutes" | All | |
| 7 (14-24 Dec) | Daily short videos until 24 Dec; "still time" pins | All | Instant delivery is our edge in the final days |
| 28 Dec | **Decision day**: apply the kill rule using the stats page | | Write the result into `PROGRESS.md` |

Leave about 1 in 5 slots open for reacting to whatever gets comments.

## 5. Content drafts (ready to use)

**Video #1, "the receipts":** (screen recording of the sample book)
> Hook: "Every astrology app told me the same thing. This one shows its receipts."
> Scroll a page slowly, zoom on the ✦ line: "Venus in Gemini, 12th house. Every paragraph says which part of your chart it's based on."
> End: "Free chart preview, link in bio. $9 once, no subscription."

**Video #2, "gift idea":**
> Hook: "Gift idea for the friend who's obsessed with her rising sign."
> Show the cover with a name, the dedication page, a chapter page.
> End: "Made from her real birth time and place. You get the PDF in minutes."

**Video #3, "honest pricing":**
> Hook: "Astrology apps and surprise subscriptions, name a more iconic duo."
> "I made the opposite: one book, one payment, no account. If it doesn't feel personal, full refund."

**Video #4, "reading the chart in the comments":** reply to a comment with the person's (permission given) Sun/Moon/rising from the free preview.

**Video #5, "what the 12th house means":** 30-second explainer using the sample wheel, ending with "your book explains every house in your chart."

**Pinterest pin text:** "Personalized birth-chart book: a thoughtful gift for astrology lovers. Written from their exact birth time and place. Instant PDF, prints like a paperback." Images: cover mockup, a chapter spread, the chart page.

**r/AppIdeas follow-up (outline):** the original idea post → why I picked it (ranked top for profit potential) → what was hard (historical time zones, making AI text specific rather than generic) → the "every paragraph cites its placement" rule → link to the sample book → "I'd love blunt feedback on whether you'd pay for this." Make sure the community allows follow-ups first.

**Friends message:** "I made a thing! It writes a birth-chart book from someone's exact birth time and place. Here's a sample (link). Would you honestly buy this as a gift? Brutal feedback welcome."

## 6. Content still needed

| Asset | Priority | Notes |
|---|---|---|
| Real domain + live Stripe + Anthropic key | Must | Owner decision: brand name first |
| 6 launch videos | Must | Phone screen recordings of the sample PDF are enough |
| 10 Pinterest pins | Must | 3 designs ready in `marketing/` (`pin-*.png`); make variations by editing `scripts/make_marketing_images.py` |
| Instagram posts | Nice | 2 ready in `marketing/` (`ig-*.png`) |
| Link preview card | Done | `marketing/og-card.png`, used automatically when the site is shared |
| Book cover mockup photo | Nice | A printed copy on a table looks more real than a screen |
| 3-5 real customer quotes | Nice | Ask the first buyers; add to the landing page |

## 7. How we measure

| Metric | Target by 24 Dec | Where |
|---|---|---|
| **Paid orders** (primary) | 5+ (kill rule); 20+ is a strong yes | Stats page |
| Visitors from tagged links | ~1,000 | Stats page, by tag |
| Visitor → free preview | 10%+ | Stats page |
| Preview → paid | 5%+ | Stats page |
| Refunds | under 1 in 20 orders | Stripe dashboard |
| Best channel | the tag with the most paid orders | Stats page, by tag |

Check the stats page every Sunday and write 3 lines in `PROGRESS.md`: numbers, what worked, what changes next week.

## 8. Risks

| Risk | What we do |
|---|---|
| Videos get no views | Hooks matter more than editing: test 3 new opening lines a week, repost the best performer |
| Visitors come but don't buy | Look at where they stop: preview but no purchase means the price or trust is off (try $19, or add customer quotes); no previews means the landing page isn't convincing |
| Reddit backlash | Only post where self-promotion is allowed; be the founder, not an ad |
| AI writes something off-key for a real customer | Read the first 10 books before they're delivered (a manual check can be added in one line); refund generously |

## 9. Next steps (owner)

1. Pick the brand name and check the domain and social handles are free.
2. Decide the launch price ($9 suggested, or test $19).
3. Create Stripe and Anthropic accounts; I'll walk through connecting them.
4. Pick hosting (see `docs/DEPLOY.md`).
5. Record the first 6 videos.
