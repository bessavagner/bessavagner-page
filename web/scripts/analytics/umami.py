"""Load the Umami CSV export and count custom events (ctx 05 §2).

Umami = reach/raw-count truth. To reconcile against GA4 you filter
website_event by event_name and count rows within the window.
"""
from __future__ import annotations

import csv
import os
from datetime import date, datetime

REQUIRED_COLUMNS = {"event_type", "event_name", "created_at"}

# Canonical name -> accepted Umami labels. Epic A migrated wiring to snake_case,
# but historical rows may still carry the legacy hyphen label, so we count both.
CONVERSION_EVENTS: dict[str, list[str]] = {
    "cv_download": ["cv_download", "cv-download"],
    "whatsapp_click": ["whatsapp_click", "whatsapp-click"],
    "generate_lead": ["generate_lead", "contact-form-submit", "contact_submit"],
    "newsletter_signup": ["newsletter_signup"],
}


class SchemaError(Exception):
    """Raised when the Umami export is missing a required column."""


def load_website_events(umami_dir: str) -> list[dict[str, str]]:
    path = os.path.join(umami_dir, "website_event.csv")
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - header
        if missing:
            raise SchemaError(
                f"{path} is missing required column(s): {sorted(missing)}. "
                f"Umami export schema changed — see ctx 05 §2."
            )
        return list(reader)


def _to_date(value: str) -> date:
    # Umami created_at is an ISO-ish timestamp, e.g. 2026-08-01T10:00:00Z.
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def count_event(rows: list[dict[str, str]], names: list[str], start: date, end: date) -> int:
    wanted = set(names)
    return sum(
        1
        for r in rows
        if r.get("event_name") in wanted and start <= _to_date(r["created_at"]) <= end
    )
