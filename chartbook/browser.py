"""Headless Chromium for turning HTML into PDF and screenshots.

Set CHROMIUM_PATH to use a specific browser binary; otherwise Playwright's own
downloaded browser is used (run `playwright install chromium` once).
"""

import os
from contextlib import contextmanager


@contextmanager
def chromium():
    from playwright.sync_api import sync_playwright

    path = os.environ.get("CHROMIUM_PATH") or None
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=path)
        try:
            yield browser
        finally:
            browser.close()
