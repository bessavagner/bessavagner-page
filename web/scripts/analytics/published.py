"""What went live this month — the URL list for the GSC indexation check.

This module deliberately does NOT decide whether a post is visible. That rule
lives in web/src/lib/publication.ts, which says (lines 5-7) that four previous
copies of it drifted apart and caused every publishing incident to date. A fifth
copy, in Python, would be exactly that mistake again. So we shell out to
`pnpm post:status` — which derives its verdict from publication.ts — and only
read the answer.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import date, datetime

from window import Window

SITE = "https://bessavagner.com"

# Content collection -> public route. Verified against built dist/ output:
#   blog/<slug>.mdx                    -> /blog/<slug>/
#   buildlog/<project>/<nn-slug>.mdx   -> /building/<project>/<nn-slug>/
# The NN- prefix is part of the live buildlog slug (splitUpdateId in
# buildlog-core.ts:37 splits the collection id at the FIRST slash only).
_ROUTES = {"blog": "blog", "buildlog": "building"}
_CONTENT_ROOT = "web/src/content/"


class StatusError(Exception):
    """Raised when `pnpm post:status` output cannot be trusted."""


@dataclass
class Post:
    state: str
    repo_path: str
    pub_date: date


def parse_status(text: str) -> list[Post]:
    posts: list[Post] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        fields = [f for f in line.split("  ") if f.strip()]
        if len(fields) != 3:
            raise StatusError(
                f"cannot parse `pnpm post:status` line {line!r} — expected "
                f"'state  repoPath  pubDateISO' (web/scripts/post.ts:119). "
                f"Did the CLI's output format change?"
            )
        state, repo_path, iso = (f.strip() for f in fields)
        pub = datetime.fromisoformat(iso.replace("Z", "+00:00")).date()
        posts.append(Post(state, repo_path, pub))
    return posts


def to_url(repo_path: str, site: str = SITE) -> str:
    if not repo_path.startswith(_CONTENT_ROOT):
        raise StatusError(f"{repo_path!r} is not under {_CONTENT_ROOT}")
    rel = repo_path[len(_CONTENT_ROOT):]
    collection, _, rest = rel.partition("/")
    route = _ROUTES.get(collection)
    if route is None or not rest:
        raise StatusError(
            f"no public route known for collection {collection!r} ({repo_path!r}) — "
            f"known collections: {sorted(_ROUTES)}"
        )
    slug = rest.removesuffix(".mdx")
    return f"{site}/{route}/{slug}/"


def published_in(text: str, w: Window, site: str = SITE) -> list[str]:
    """Live URLs whose pubDate falls inside the window.

    `state == "published"` is the CLI's word for live. `review`, `draft` and
    `stale-approval` are all NOT live and are excluded — a stale-approval post
    is an approved post whose content changed, so it is hidden in prod.
    """
    return [
        to_url(p.repo_path, site)
        for p in parse_status(text)
        if p.state == "published" and w.start <= p.pub_date <= w.end
    ]


def run_post_status(repo_root: str) -> str:
    """Shell out to the real CLI. Runs from web/ where package.json lives."""
    proc = subprocess.run(
        ["pnpm", "-s", "post:status"],
        cwd=f"{repo_root}/web",
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise StatusError(
            f"`pnpm post:status` failed (exit {proc.returncode}): {proc.stderr.strip()}"
        )
    return proc.stdout
