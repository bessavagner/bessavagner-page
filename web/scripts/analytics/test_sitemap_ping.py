import contextlib
import io
import unittest

import sitemap_ping


class FakeSitemapsList:
    def __init__(self, sitemaps):
        self._sitemaps = sitemaps

    def execute(self):
        return {"sitemap": self._sitemaps}


class FakeSitemaps:
    def __init__(self, sitemaps):
        self._sitemaps = sitemaps

    def list(self, siteUrl):  # noqa: N803 — Google's API spells it this way
        return FakeSitemapsList(self._sitemaps)


class FakeClient:
    def __init__(self, sitemaps):
        self._sitemaps = FakeSitemaps(sitemaps)

    def sitemaps(self):
        return self._sitemaps


class PrintState(unittest.TestCase):
    def test_prints_label_path_lastdownloaded_and_submitted(self):
        client = FakeClient([{
            "path": "https://bessavagner.com/sitemap-index.xml",
            "lastDownloaded": "2026-07-08T09:00:00.000Z",
            "contents": [{"type": "web", "submitted": "65", "indexed": "60"}],
        }])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sitemap_ping._print_state(client, "sc-domain:bessavagner.com", "BEFORE")
        out = buf.getvalue()
        self.assertIn("--- BEFORE ---", out)
        self.assertIn("https://bessavagner.com/sitemap-index.xml", out)
        self.assertIn("lastDownloaded=2026-07-08T09:00:00.000Z", out)
        self.assertIn("submitted=65", out)

    def test_never_downloaded_sitemap_prints_never_not_blank(self):
        client = FakeClient([{"path": "https://bessavagner.com/sitemap-index.xml"}])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sitemap_ping._print_state(client, "s", "AFTER")
        self.assertIn("lastDownloaded=never", buf.getvalue())

    def test_no_sitemaps_registered_says_so_explicitly(self):
        client = FakeClient([])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sitemap_ping._print_state(client, "s", "BEFORE")
        self.assertIn("no sitemaps registered", buf.getvalue())


class DefaultSitemapUrl(unittest.TestCase):
    def test_defaults_to_the_live_sitemap_index(self):
        self.assertEqual(
            sitemap_ping.DEFAULT_SITEMAP_URL, "https://bessavagner.com/sitemap-index.xml"
        )


if __name__ == "__main__":
    unittest.main()
