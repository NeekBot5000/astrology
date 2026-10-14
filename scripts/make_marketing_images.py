"""Make Pinterest pins and Instagram posts from the sample book.

Run:  CHROMIUM_PATH=... python scripts/make_marketing_images.py
Needs `pdftoppm` (from poppler-utils) to turn book pages into images.
Writes PNGs to marketing/. Re-run after changing the brand name or the sample book.
"""

import base64
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from chartbook.book import BRAND  # noqa: E402
from chartbook.browser import chromium  # noqa: E402

PDF = ROOT / "samples/maya-sample.pdf"
OUT = ROOT / "marketing"
FONTS = (ROOT / "chartbook/static/fonts/fonts.css").read_text()


def page_png(page: int, tmp: Path, dpi: int = 150) -> str:
    """Render one PDF page and return it as a data URI."""
    stem = tmp / f"p{page}"
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", "-singlefile", "-f", str(page), "-l", str(page), str(PDF), str(stem)], check=True)
    return "data:image/png;base64," + base64.b64encode(stem.with_suffix(".png").read_bytes()).decode()


def font_css() -> str:
    def embed(name: str) -> str:
        return "data:font/woff2;base64," + base64.b64encode((ROOT / "chartbook/static/fonts" / name).read_bytes()).decode()

    css = FONTS
    for name in ("CormorantGaramond.woff2", "CormorantGaramond-Italic.woff2", "SourceSerif4.woff2", "SourceSerif4-Italic.woff2"):
        css = css.replace(f"url({name})", f"url({embed(name)})")
    return css


BASE_CSS = """
* { box-sizing: border-box; margin: 0; }
body { width: %(w)dpx; height: %(h)dpx; overflow: hidden; font-family: "Source Serif 4", serif;
  background: radial-gradient(circle at 70%% 20%%, #2d3566, #1c2140 60%%); color: #f3ead2; }
.wrap { position: absolute; inset: 0; padding: %(pad)dpx; display: flex; flex-direction: column; }
h1 { font-family: "Cormorant Garamond", serif; font-weight: 500; color: #e8d7a8; line-height: 1.02; }
.brand { font-size: 22px; letter-spacing: .3em; text-transform: uppercase; color: #d9bf78; }
.foot { margin-top: auto; font-size: 26px; color: #e6e0cf; }
.foot b { color: #e8d7a8; }
.page { background: #fff; box-shadow: 0 30px 80px rgba(0,0,0,.45); border-radius: 4px; }
.star { color: #d9bf78; }
"""

DESIGNS = {
    # Pinterest pins: 1000 x 1500
    "pin-written-for-one-person": (1000, 1500, """
      <div class="brand">{brand}</div>
      <h1 style="font-size:92px;margin:28px 0 22px">A birth-chart book written for one person</h1>
      <p style="font-size:30px;line-height:1.4;max-width:820px">From their exact birth time and place. Every paragraph shows which part of their chart it comes from.</p>
      <div style="position:relative;flex:1;margin-top:40px">
        <img class="page" src="{p3}" style="position:absolute;width:430px;left:360px;top:70px;transform:rotate(5deg)">
        <img class="page" src="{p1}" style="position:absolute;width:430px;left:90px;top:20px;transform:rotate(-4deg)">
      </div>
      <div class="foot"><b>Free chart preview</b> · $29 once · instant PDF</div>
    """),
    "pin-gift-idea": (1000, 1500, """
      <div class="brand">Gift idea</div>
      <h1 style="font-size:84px;margin:28px 0 22px">For the friend who's obsessed with her rising sign</h1>
      <div style="position:relative;flex:1;margin-top:30px">
        <img class="page" src="{p2}" style="position:absolute;width:420px;left:440px;top:80px;transform:rotate(4deg)">
        <img class="page" src="{p1}" style="position:absolute;width:420px;left:110px;top:30px;transform:rotate(-3deg)">
      </div>
      <p style="font-size:30px;line-height:1.4">Her own chart wheel on the cover, your words on the first page, seven chapters about her.</p>
      <div class="foot" style="margin-top:28px"><b>{brand}</b> · delivered in minutes</div>
    """),
    "pin-shows-its-receipts": (1000, 1500, """
      <div class="brand">{brand}</div>
      <h1 style="font-size:96px;margin:28px 0 30px">Astrology that shows its receipts</h1>
      <div style="flex:1;overflow:hidden;border-radius:6px" class="page">
        <img src="{p11}" style="width:1020px;margin:-50px 0 0 -105px">
      </div>
      <p style="font-size:30px;line-height:1.4;margin-top:34px"><span class="star">✦</span> Under every paragraph: the exact placement it's based on. No generic Sun-sign filler.</p>
      <div class="foot" style="margin-top:24px">$29 once · no subscription · free preview</div>
    """),
    # Link preview card for chats and social sites (Open Graph): 1200 x 630
    "og-card": (1200, 630, """
      <div style="display:flex;gap:60px;height:100%;align-items:center">
        <img class="page" src="{p1}" style="width:300px;transform:rotate(-3deg)">
        <div>
          <div class="brand">{brand}</div>
          <h1 style="font-size:74px;margin:20px 0 20px">A birth-chart book written for one person</h1>
          <p style="font-size:28px;line-height:1.4">Free chart preview · $29 once · instant PDF</p>
        </div>
      </div>
    """),
    # Instagram square posts: 1080 x 1080
    "ig-pay-once": (1080, 1080, """
      <div class="brand">{brand}</div>
      <h1 style="font-size:104px;margin:40px 0 30px">Pay once.<br>Seriously.</h1>
      <p style="font-size:36px;line-height:1.45;max-width:860px">One personalized birth-chart book. No subscription, no account, no surprise charges. Full refund within 14 days if it doesn't feel personal.</p>
      <div class="foot"><b>$29</b> · free chart preview first</div>
    """),
    "ig-sample-page": (1080, 1080, """
      <div style="display:flex;gap:56px;height:100%;align-items:center">
        <img class="page" src="{p4}" style="width:470px;transform:rotate(-2deg)">
        <div>
          <div class="brand">{brand}</div>
          <h1 style="font-size:76px;margin:24px 0 24px">Their real sky, the moment they were born</h1>
          <p style="font-size:30px;line-height:1.45">Chart wheel, every planet's sign and house, and 22 pages written from it.</p>
        </div>
      </div>
    """),
}


def main() -> None:
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        pages = {f"p{n}": page_png(n, tmp, dpi=110 if n != 11 else 170) for n in (1, 2, 3, 4, 11)}
        with chromium() as browser:
            for name, (w, h, body) in DESIGNS.items():
                pad = {1000: 80, 1080: 90}.get(w, 60)
                html = (
                    f"<!doctype html><html><head><meta charset='utf-8'><style>{font_css()}"
                    f"{BASE_CSS % {'w': w, 'h': h, 'pad': pad}}</style></head>"
                    f"<body><div class='wrap'>{body.format(brand=BRAND, **pages)}</div></body></html>"
                )
                page = browser.new_page(viewport={"width": w, "height": h})
                page.set_content(html, wait_until="load")
                page.screenshot(path=str(OUT / f"{name}.png"))
                page.close()
                print("wrote", OUT / f"{name}.png")
    # The website uses the link preview card directly.
    (ROOT / "chartbook/web/static/og.png").write_bytes((OUT / "og-card.png").read_bytes())


if __name__ == "__main__":
    main()
