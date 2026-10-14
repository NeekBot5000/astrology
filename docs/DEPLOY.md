# Putting the site online

Plain-language guide. "Hosting" means renting a computer on the internet that runs the website all day.

## What you need (about $10-20/month plus usage)

| Thing | What it is | Cost |
|---|---|---|
| A host that runs Docker containers and has a **persistent disk** | Where the site runs. A "persistent disk" keeps orders and books when the site restarts. Render, Railway and Fly.io all work. | ~$7-15/month |
| A domain name | The web address, e.g. birthskybooks.com (check the name first) | ~$12/year |
| Stripe account | Takes card payments; pays out to your bank | 2.9% + 30¢ per sale |
| Anthropic API key | Writes the books | ~$0.30-0.80 per book |

The site is packaged as a **Docker image** (a sealed box containing the code and everything it needs, including the browser that makes PDFs). The `Dockerfile` in this repo describes the box; the host builds it for you.

## Steps (Render as the example; others are similar)

1. **Create the service.** In Render: New → Web Service → connect this GitHub repo → it detects the Dockerfile. Pick the smallest paid instance (the free tier sleeps and has no disk).
2. **Add a disk.** In the service settings, add a disk mounted at `/data`, 1 GB is plenty.
3. **Set environment variables** (the settings the code reads, listed in `.env.example`):
   - `BASE_URL`: your address, e.g. `https://birthskybooks.com`
   - `DATA_DIR`: `/data`
   - `ANTHROPIC_API_KEY`: from console.anthropic.com → API keys
   - `SUPPORT_EMAIL`: an inbox you read
   - `ADMIN_TOKEN`: a long random password for the stats and review pages
   - `REVIEW_BOOKS`: `true` for your first ~10 orders, so you read each book at `/admin/review` before the customer can download it
   - Leave `STRIPE_SECRET_KEY` empty at first: the site then runs in **"reserve a copy"** mode (collects emails, takes no money). Good for a first look.
4. **Turn on payments.** In Stripe, copy the secret key (starts `sk_live_`, or `sk_test_` to practise) into `STRIPE_SECRET_KEY`. Then in Stripe → Developers → Webhooks → add endpoint `https://YOUR-DOMAIN/stripe/webhook`, choose the events `checkout.session.completed` and `checkout.session.async_payment_succeeded`, and copy its signing secret into `STRIPE_WEBHOOK_SECRET`.
5. **Connect the domain.** Render → Settings → Custom domain, then add the DNS record it shows at your domain registrar.
6. **Check the writer first.** On your own computer with the key set: `python scripts/check_writer.py` (about $0.25). It writes three test chapters; read them in `output/`.
7. **Test with real money once.** Order a book for yourself, check the PDF, then refund yourself in Stripe. This proves payment → writing → download works end to end.

## Running it on your own computer (optional)

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/playwright install chromium
cp .env.example .env        # then fill in what you have
set -a; . ./.env; set +a
.venv/bin/uvicorn chartbook.web.app:app --reload
```
Then open http://localhost:8000.

## Good to know

- **One server, one process.** Books are written in the background inside the web process. That's fine for hundreds of orders a day. If sales take off, move writing to a separate worker.
- **Stats page:** `https://YOUR-DOMAIN/admin/stats`. Your browser asks for a username and password: type anything as the username and your `ADMIN_TOKEN` as the password.
- **Data:** orders and books are erased automatically `KEEP_DAYS` (30) days after delivery. Back up nothing personal; there's nothing to keep.
- **Not verified yet:** the Docker image hasn't been built in the development sandbox (no Docker engine there). The first deploy is the test; if it fails, the build log will say why.
