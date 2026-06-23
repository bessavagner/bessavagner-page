"""Load portfolio content from the single source of truth (content/projects.json).

The same JSON seeds the Astro content collection in Phase 2, so keep this loader
thin and the schema stable (see content/projects.schema.json).
"""
import json
import logging

from app.settings import CONTENT_DIR, DEBUG

logger = logging.getLogger("content")

_CACHE: dict | None = None


def _load_from_disk() -> dict:
    path = CONTENT_DIR / "projects.json"
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    projects = sorted(
        data.get("projects", []), key=lambda p: p.get("order", 999)
    )
    return {
        "profile": data.get("profile", {}),
        "featured": [p for p in projects if p.get("featured")],
        "cards": [p for p in projects if not p.get("featured")],
    }


def load_content() -> dict:
    """Return portfolio content. Cached in production; re-read in DEBUG."""
    global _CACHE
    if DEBUG:
        return _load_from_disk()
    if _CACHE is None:
        _CACHE = _load_from_disk()
    return _CACHE
