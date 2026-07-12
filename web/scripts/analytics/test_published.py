import unittest
from datetime import date

import published
from window import Window

# Real shape of `pnpm post:status` output (web/scripts/post.ts:119):
#   state<2 spaces>repoPath<2 spaces>pubDateISO
SAMPLE = """published  web/src/content/blog/sub-second-llm-triage.mdx  2026-07-05T08:00:00.000Z
published  web/src/content/buildlog/regwatch/04-deploying-regwatch-to-cloud-run.mdx  2026-07-09T11:00:00.000Z
review  web/src/content/blog/real-time-websockets-with-django-channels.mdx  2026-07-11T08:00:00.000Z
draft  web/src/content/blog/pruning-chat-context-by-summarization.mdx  2026-07-13T08:00:00.000Z
published  web/src/content/blog/beating-browser-fingerprinting.mdx  2026-06-29T00:00:00.000Z
"""


class ParseStatus(unittest.TestCase):
    def test_parses_all_rows(self):
        posts = published.parse_status(SAMPLE)
        self.assertEqual(len(posts), 5)
        self.assertEqual(posts[0].state, "published")
        self.assertEqual(posts[0].pub_date, date(2026, 7, 5))

    def test_blank_lines_ignored(self):
        self.assertEqual(published.parse_status("\n\n"), [])

    def test_malformed_line_raises(self):
        with self.assertRaises(published.StatusError):
            published.parse_status("garbage-with-no-columns\n")


class ToUrl(unittest.TestCase):
    def test_blog_maps_to_blog_slug(self):
        self.assertEqual(
            published.to_url("web/src/content/blog/sub-second-llm-triage.mdx"),
            "https://bessavagner.com/blog/sub-second-llm-triage/",
        )

    def test_buildlog_maps_to_building_project_slug_keeping_numeric_prefix(self):
        # Confirmed against dist/: the NN- prefix IS part of the live slug.
        self.assertEqual(
            published.to_url("web/src/content/buildlog/regwatch/04-deploying-regwatch-to-cloud-run.mdx"),
            "https://bessavagner.com/building/regwatch/04-deploying-regwatch-to-cloud-run/",
        )

    def test_unknown_collection_raises(self):
        with self.assertRaises(published.StatusError):
            published.to_url("web/src/content/notes/whatever.mdx")


class PublishedIn(unittest.TestCase):
    def _july(self):
        return Window(date(2026, 7, 1), date(2026, 7, 31))

    def test_only_live_posts_inside_the_window(self):
        urls = published.published_in(SAMPLE, self._july())
        self.assertEqual(urls, [
            "https://bessavagner.com/blog/sub-second-llm-triage/",
            "https://bessavagner.com/building/regwatch/04-deploying-regwatch-to-cloud-run/",
        ])

    def test_excludes_review_and_draft(self):
        urls = published.published_in(SAMPLE, self._july())
        self.assertNotIn("https://bessavagner.com/blog/real-time-websockets-with-django-channels/", urls)
        self.assertNotIn("https://bessavagner.com/blog/pruning-chat-context-by-summarization/", urls)

    def test_excludes_posts_outside_the_month(self):
        urls = published.published_in(SAMPLE, self._july())
        self.assertNotIn("https://bessavagner.com/blog/beating-browser-fingerprinting/", urls)  # June
