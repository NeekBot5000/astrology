"""Settings, all read from environment variables (see .env.example)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    base_url: str
    data_dir: Path
    price_cents: int
    currency: str
    stripe_secret_key: str | None
    stripe_webhook_secret: str | None
    anthropic_configured: bool
    keep_days: int  # how long finished books and birth details are kept
    support_email: str
    admin_token: str | None = None
    review_books: bool = False  # owner approves each book before the customer can download it

    @property
    def payments_enabled(self) -> bool:
        return bool(self.stripe_secret_key)

    @property
    def price_text(self) -> str:
        return f"${self.price_cents / 100:.0f}" if self.price_cents % 100 == 0 else f"${self.price_cents / 100:.2f}"


def load_settings() -> Settings:
    env = os.environ
    data_dir = Path(env.get("DATA_DIR", "data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return Settings(
        base_url=env.get("BASE_URL", "http://localhost:8000").rstrip("/"),
        data_dir=data_dir,
        price_cents=int(env.get("PRICE_CENTS", "2900")),
        currency=env.get("CURRENCY", "usd"),
        stripe_secret_key=env.get("STRIPE_SECRET_KEY") or None,
        stripe_webhook_secret=env.get("STRIPE_WEBHOOK_SECRET") or None,
        anthropic_configured=bool(env.get("ANTHROPIC_API_KEY") or env.get("ANTHROPIC_AUTH_TOKEN")),
        keep_days=int(env.get("KEEP_DAYS", "30")),
        support_email=env.get("SUPPORT_EMAIL", "support@example.com"),
        admin_token=env.get("ADMIN_TOKEN") or None,
        review_books=env.get("REVIEW_BOOKS", "").lower() in ("1", "true", "yes"),
    )
