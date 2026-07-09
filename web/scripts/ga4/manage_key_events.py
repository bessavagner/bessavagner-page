#!/usr/bin/env python3
"""Reconcile the bessavagner.com GA4 key-event set, reproducibly.

Read-only by default: prints the current key events and the planned changes.
Pass --apply to WRITE to the live GA4 property (owner-gated — see the sprint
doc). Needs a service account (or ADC) with the analytics.edit scope and
Editor/Administrator on the property.

Setup (from web/scripts/ga4/):
    python -m venv .venv && . .venv/bin/activate
    pip install -r requirements.txt
    export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

Usage:
    python manage_key_events.py            # dry-run (safe)
    python manage_key_events.py --apply    # perform create/delete (owner-gated)

The DESIRED set below mirrors only the CONVERSION events from
web/src/lib/analytics-events.ts (generate_lead, whatsapp_click, newsletter_signup, cv_download) — the taxonomy's engagement events (hero_cta_*, email_click) are intentionally NOT key events. Keep this set in sync by hand.
"""
from __future__ import annotations

import argparse
import os

from google.analytics.admin import AnalyticsAdminServiceClient
from google.analytics.admin_v1beta.types import KeyEvent

# Canonical events this site actually fires and wants marked as key events.
DESIRED_KEY_EVENTS = {
    "generate_lead",
    "whatsapp_click",
    "newsletter_signup",
    "cv_download",
}
# Recommended events GA4 pre-created that this static site will never fire.
DEAD_KEY_EVENTS = {"qualify_lead", "close_convert_lead"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write to live GA4 (owner-gated); default is a dry run",
    )
    args = parser.parse_args()

    property_id = os.environ.get("GA4_PROPERTY_ID", "543524687")
    parent = f"properties/{property_id}"
    client = AnalyticsAdminServiceClient()

    existing = {ke.event_name: ke for ke in client.list_key_events(parent=parent)}
    print(f"Property {property_id}: {len(existing)} key event(s) currently marked")
    for name, ke in sorted(existing.items()):
        print(f"  - {name:20} {ke.counting_method.name:16} deletable={ke.deletable}")

    to_create = sorted(DESIRED_KEY_EVENTS - existing.keys())
    to_delete = sorted(DEAD_KEY_EVENTS & existing.keys())

    print("\nPlanned changes:")
    for name in to_create:
        print(f"  + create key event {name} (ONCE_PER_EVENT)")
    for name in to_delete:
        ke = existing[name]
        verb = "delete" if ke.deletable else "SKIP (not deletable — unmark in the GA4 UI)"
        print(f"  - {verb}: {name}")
    if not to_create and not to_delete:
        print("  (none — the key-event set already matches)")

    if not args.apply:
        print("\nDry run. Re-run with --apply to write to live GA4.")
        return 0

    for name in to_create:
        created = client.create_key_event(
            parent=parent,
            key_event=KeyEvent(
                event_name=name,
                counting_method=KeyEvent.CountingMethod.ONCE_PER_EVENT,
            ),
        )
        print(f"created {created.name}")
    for name in to_delete:
        ke = existing[name]
        if ke.deletable:
            client.delete_key_event(name=ke.name)
            print(f"deleted {ke.name}")
        else:
            print(f"skip {name}: not deletable via API — unmark it in the GA4 UI")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
