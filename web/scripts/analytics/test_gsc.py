import unittest
from datetime import date

import gsc
from googleapiclient.errors import HttpError
from window import Window


class FakeQuery:
    """Stands in for service.searchanalytics().query(...)."""

    def __init__(self, rows):
        self._rows = rows

    def execute(self):
        return {"rows": self._rows} if self._rows else {}


class FakeSearchAnalytics:
    def __init__(self, rows_by_dim):
        self.rows_by_dim = rows_by_dim
        self.last_body = None

    def query(self, siteUrl, body):  # noqa: N803 — Google's API spells it this way
        self.last_body = body
        key = tuple(body.get("dimensions", []))
        rows = self.rows_by_dim.get(key, [])
        # Honor rowLimit exactly as the real Search Analytics API does: it
        # truncates server-side, before any client-side sort ever runs.
        limit = body.get("rowLimit")
        if limit is not None:
            rows = rows[:limit]
        return FakeQuery(rows)


class FakeClient:
    def __init__(self, rows_by_dim=None):
        self._sa = FakeSearchAnalytics(rows_by_dim or {})

    def searchanalytics(self):
        return self._sa


JULY = Window(date(2026, 7, 1), date(2026, 7, 31))


class FetchCoverage(unittest.TestCase):
    def test_detects_true_range_when_month_is_partial(self):
        # GSC lags ~2 days: July has data only through the 10th.
        client = FakeClient({("date",): [
            {"keys": ["2026-07-01"], "clicks": 0, "impressions": 5, "ctr": 0.0, "position": 20.0},
            {"keys": ["2026-07-10"], "clicks": 1, "impressions": 9, "ctr": 0.11, "position": 18.0},
        ]})
        cov = gsc.fetch_coverage(client, "sc-domain:example.com", JULY)
        self.assertEqual(cov.start, date(2026, 7, 1))
        self.assertEqual(cov.end, date(2026, 7, 10))  # NOT July 31

    def test_no_rows_returns_none_not_an_empty_window(self):
        # A month predating GSC data must be flagged, never zero-filled.
        self.assertIsNone(gsc.fetch_coverage(FakeClient(), "sc-domain:example.com", JULY))

    def test_query_is_scoped_to_the_requested_window(self):
        client = FakeClient({("date",): [
            {"keys": ["2026-07-03"], "clicks": 0, "impressions": 1, "ctr": 0.0, "position": 9.0},
        ]})
        gsc.fetch_coverage(client, "sc-domain:example.com", JULY)
        body = client.searchanalytics().last_body
        self.assertEqual(body["startDate"], "2026-07-01")
        self.assertEqual(body["endDate"], "2026-07-31")


class FetchTotals(unittest.TestCase):
    def _client(self):
        # Shape of the real 90-day pull taken on 2026-07-12.
        return FakeClient({(): [
            {"clicks": 3, "impressions": 567, "ctr": 0.00529, "position": 23.3},
        ]})

    def test_emits_four_totals_all_sourced_gsc(self):
        metrics = gsc.fetch_totals(self._client(), "sc-domain:example.com", JULY)
        self.assertEqual([m.name for m in metrics],
                         ["Clicks", "Impressions", "CTR", "Average position"])
        self.assertTrue(all(m.source == "GSC" for m in metrics))

    def test_values_are_formatted(self):
        by_name = {m.name: m.value for m in gsc.fetch_totals(self._client(), "s", JULY)}
        self.assertEqual(by_name["Clicks"], "3")
        self.assertEqual(by_name["Impressions"], "567")
        self.assertEqual(by_name["CTR"], "0.53%")
        self.assertEqual(by_name["Average position"], "23.3")

    def test_position_carries_the_low_volume_caveat_as_a_note(self):
        pos = [m for m in gsc.fetch_totals(self._client(), "s", JULY)
               if m.name == "Average position"][0]
        self.assertIn("impression-weighted", pos.note)

    def test_no_rows_yields_no_metrics_not_zeros(self):
        # Absence of measurement is never a measured zero.
        self.assertEqual(gsc.fetch_totals(FakeClient(), "s", JULY), [])


class FetchBreakdowns(unittest.TestCase):
    def test_top_queries(self):
        client = FakeClient({("query",): [
            {"keys": ["fingerprint browser selenium"], "clicks": 0, "impressions": 4,
             "ctr": 0.0, "position": 17.2},
        ]})
        m = gsc.fetch_top_queries(client, "s", JULY)[0]
        self.assertEqual(m.name, "fingerprint browser selenium")
        self.assertEqual(m.source, "GSC")
        self.assertIn("4 impr", m.value)
        self.assertIn("pos 17.2", m.value)

    def test_top_pages(self):
        client = FakeClient({("page",): [
            {"keys": ["https://bessavagner.com/blog/beating-browser-fingerprinting/"],
             "clicks": 1, "impressions": 179, "ctr": 0.0056, "position": 18.6},
        ]})
        m = gsc.fetch_top_pages(client, "s", JULY)[0]
        self.assertEqual(m.name, "/blog/beating-browser-fingerprinting/")  # host stripped
        self.assertIn("179 impr", m.value)

    def test_countries(self):
        client = FakeClient({("country",): [
            {"keys": ["bra"], "clicks": 0, "impressions": 48, "ctr": 0.0, "position": 30.0},
            {"keys": ["nld"], "clicks": 1, "impressions": 21, "ctr": 0.048, "position": 15.0},
        ]})
        metrics = gsc.fetch_countries(client, "s", JULY)
        self.assertEqual([m.name for m in metrics], ["BRA", "NLD"])
        self.assertTrue(all(m.source == "GSC" for m in metrics))

    def test_top_queries_ranks_by_impressions_not_the_apis_click_order(self):
        # Real GSC behavior (verified live, 2026-07-12, 90-day window): the
        # Search Analytics API has no orderBy. rowLimit truncates
        # server-side by CLICKS descending, and on this site every query
        # ties on zero clicks, so the API's own tie-break is alphabetical.
        # A naive rowLimit=10 fetch would only ever see "query a".."query
        # j" — the true #1 query by impressions sorts alphabetically after
        # all of them and would be truncated away before any local sort
        # could rescue it.
        low_impression_alphabetical_rows = [
            {"keys": [f"query {c}"], "clicks": 0, "impressions": i + 1,
             "ctr": 0.0, "position": 20.0}
            for i, c in enumerate("abcdefghijk")  # 11 rows: "query a".."query k"
        ]
        true_top_query_by_impressions = {
            "keys": ["unstructured data extraction"], "clicks": 0,
            "impressions": 22, "ctr": 0.0, "position": 5.0,
        }
        # 12 rows total, in the alphabetical order the live API actually
        # returns for all-zero-click ties — the high-impression row last.
        rows = low_impression_alphabetical_rows + [true_top_query_by_impressions]
        client = FakeClient({("query",): rows})

        metrics = gsc.fetch_top_queries(client, "s", JULY, limit=10)

        names = [m.name for m in metrics]
        self.assertIn("unstructured data extraction", names)
        self.assertEqual(names[0], "unstructured data extraction")
        self.assertEqual(len(metrics), 10)

    def test_breakdown_at_the_fetch_ceiling_raises_instead_of_ranking(self):
        # If a dimension's true row count ever reaches _BREAKDOWN_FETCH_LIMIT,
        # the API's server-side truncation (clicks descending, no orderBy)
        # kicks in exactly as it did at limit=1000 in the bug this module was
        # built to prevent. A response landing exactly on the ceiling is
        # indistinguishable from "truncated" and must never be silently
        # ranked by impressions and sliced — that would be a click-biased
        # top-N presented as if it were complete. Built from the constant
        # itself so this stays correct if the ceiling ever changes.
        rows = [
            {"keys": [f"query {i}"], "clicks": 0, "impressions": i,
             "ctr": 0.0, "position": 20.0}
            for i in range(gsc._BREAKDOWN_FETCH_LIMIT)
        ]
        client = FakeClient({("query",): rows})
        with self.assertRaises(gsc.TruncationError):
            gsc.fetch_top_queries(client, "s", JULY)

    def test_fetch_page_rows_returns_every_row_unsliced(self):
        # The pinned-page watchlist looks pages up BY NAME, so it needs the
        # whole breakdown — a top-10 slice is exactly what it exists to escape.
        rows = [
            {"keys": [f"https://bessavagner.com/blog/p{i}/"], "clicks": 0,
             "impressions": 100 - i, "ctr": 0.0, "position": 20.0}
            for i in range(15)
        ]
        client = FakeClient({("page",): rows})
        out = gsc.fetch_page_rows(client, "s", JULY)
        self.assertEqual(len(out), 15)  # not 10
        self.assertEqual(out[0]["keys"][0], "https://bessavagner.com/blog/p0/")

    def test_fetch_page_rows_keeps_the_truncation_guard(self):
        # Same ceiling rule as every other breakdown: a response landing exactly
        # on the fetch limit is a clicks-biased partial sample, not the dataset.
        rows = [
            {"keys": [f"https://bessavagner.com/blog/p{i}/"], "clicks": 0,
             "impressions": i, "ctr": 0.0, "position": 20.0}
            for i in range(gsc._BREAKDOWN_FETCH_LIMIT)
        ]
        client = FakeClient({("page",): rows})
        with self.assertRaises(gsc.TruncationError):
            gsc.fetch_page_rows(client, "s", JULY)


class FakeResp:
    def __init__(self, status):
        self.status = status
        self.reason = "quota"


class FakeInspectQuery:
    def __init__(self, verdict=None, error=None):
        self._verdict = verdict
        self._error = error

    def execute(self):
        if self._error:
            raise self._error
        return {"inspectionResult": {"indexStatusResult": {"coverageState": self._verdict}}}


class FakeUrlInspection:
    def __init__(self, by_url):
        self.by_url = by_url

    def index(self):
        return self

    def inspect(self, body):
        entry = self.by_url[body["inspectionUrl"]]
        return FakeInspectQuery(**entry)


class InspectClient:
    def __init__(self, by_url):
        self._ui = FakeUrlInspection(by_url)

    def urlInspection(self):  # noqa: N802 — Google's API spells it this way
        return self._ui


class InspectUrls(unittest.TestCase):
    def test_indexed_url_reports_its_coverage_state(self):
        client = InspectClient({
            "https://bessavagner.com/blog/a/": {"verdict": "Submitted and indexed"},
        })
        m = gsc.inspect_urls(client, "sc-domain:example.com", ["https://bessavagner.com/blog/a/"])[0]
        self.assertEqual(m.name, "/blog/a/")
        self.assertEqual(m.value, "Submitted and indexed")
        self.assertEqual(m.source, "GSC")

    def test_not_indexed_url_reports_not_indexed(self):
        client = InspectClient({
            "https://bessavagner.com/blog/b/": {"verdict": "Discovered - currently not indexed"},
        })
        m = gsc.inspect_urls(client, "s", ["https://bessavagner.com/blog/b/"])[0]
        self.assertEqual(m.value, "Discovered - currently not indexed")

    def test_failed_inspection_is_pending_NOT_not_indexed(self):
        # The rule that matters most: a failed lookup and an absent page are
        # OPPOSITE conclusions. Confusing them sends you rewriting a fine page.
        err = HttpError(FakeResp(429), b"quota exceeded")
        client = InspectClient({"https://bessavagner.com/blog/c/": {"error": err}})
        m = gsc.inspect_urls(client, "s", ["https://bessavagner.com/blog/c/"])[0]
        self.assertIn("pending", m.value)
        self.assertNotIn("not indexed", m.value.lower())
        self.assertIn("inspection failed", m.note.lower())

    def test_empty_url_list_yields_no_metrics(self):
        self.assertEqual(gsc.inspect_urls(InspectClient({}), "s", []), [])

    def test_missing_coverage_state_is_pending_NOT_not_indexed(self):
        # Response present, but neither 'verdict' nor 'error' — the shape the
        # API returns when coverageState is absent/empty. This branch existed
        # but had no covering test.
        client = InspectClient({
            "https://bessavagner.com/blog/d/": {},
        })
        m = gsc.inspect_urls(client, "s", ["https://bessavagner.com/blog/d/"])[0]
        self.assertEqual(m.value, "pending")
        self.assertNotIn("not indexed", m.value.lower())
        self.assertEqual(m.source, "GSC")

    def test_non_http_error_on_one_url_does_not_sink_the_batch(self):
        # A non-HttpError exception (network error, auth refresh failure,
        # unexpected shape) on ONE url must degrade THAT url to pending and
        # let the loop continue — the other urls' results must survive.
        urls = [
            "https://bessavagner.com/blog/e/",
            "https://bessavagner.com/blog/f/",
            "https://bessavagner.com/blog/g/",
        ]
        client = InspectClient({
            urls[0]: {"verdict": "Submitted and indexed"},
            urls[1]: {"error": ConnectionError("connection reset by peer")},
            urls[2]: {"verdict": "Crawled - currently not indexed"},
        })
        result = gsc.inspect_urls(client, "s", urls)

        self.assertEqual(len(result), len(urls))  # no url silently dropped

        self.assertEqual(result[0].value, "Submitted and indexed")

        self.assertEqual(result[1].value, "pending")
        self.assertNotIn("not indexed", result[1].value.lower())
        self.assertIn("ConnectionError", result[1].note)
        self.assertIn("connection reset by peer", result[1].note)

        self.assertEqual(result[2].value, "Crawled - currently not indexed")


class Fake403Query:
    def execute(self):
        raise HttpError(FakeResp(403), b"forbidden")


class Fake403SearchAnalytics:
    def query(self, siteUrl, body):  # noqa: N803 — Google's API spells it this way
        return Fake403Query()


class Fake403Client:
    def searchanalytics(self):
        return Fake403SearchAnalytics()


class QueryAccessErrors(unittest.TestCase):
    def test_403_raises_access_error(self):
        # The module's own worst failure mode: a silently-empty GSC section
        # reads as "no search demand", the most dangerous wrong answer this
        # module can give. A 403 (service account not a user on the
        # property) must raise loudly, never degrade to an empty list.
        with self.assertRaises(gsc.AccessError):
            gsc.fetch_coverage(Fake403Client(), "sc-domain:example.com", JULY)


class FakeSitemapsSubmit:
    def __init__(self, error=None):
        self._error = error

    def execute(self):
        if self._error:
            raise self._error
        return {}


class FakeSitemapsList:
    def __init__(self, sitemaps):
        self._sitemaps = sitemaps

    def execute(self):
        return {"sitemap": self._sitemaps}


class FakeSitemaps:
    def __init__(self, sitemaps=None, submit_error=None):
        self.sitemaps = sitemaps or []
        self.submit_error = submit_error
        self.last_submit_kwargs = None
        self.last_list_kwargs = None

    def submit(self, siteUrl, feedpath):  # noqa: N803 — Google's API spells it this way
        self.last_submit_kwargs = {"siteUrl": siteUrl, "feedpath": feedpath}
        return FakeSitemapsSubmit(self.submit_error)

    def list(self, siteUrl):  # noqa: N803 — Google's API spells it this way
        self.last_list_kwargs = {"siteUrl": siteUrl}
        return FakeSitemapsList(self.sitemaps)


class SitemapsClient:
    def __init__(self, sitemaps=None, submit_error=None):
        self._sitemaps = FakeSitemaps(sitemaps, submit_error)

    def sitemaps(self):
        return self._sitemaps


SITEMAP_URL = "https://bessavagner.com/sitemap-index.xml"


class SubmitSitemap(unittest.TestCase):
    def test_calls_api_with_site_and_feedpath(self):
        client = SitemapsClient()
        gsc.submit_sitemap(client, "sc-domain:bessavagner.com", SITEMAP_URL)
        kwargs = client._sitemaps.last_submit_kwargs
        self.assertEqual(kwargs["siteUrl"], "sc-domain:bessavagner.com")
        self.assertEqual(kwargs["feedpath"], SITEMAP_URL)

    def test_403_raises_access_error_not_silent_failure(self):
        # A submit that silently swallows a 403 is the dangerous case here:
        # the operator would believe Google was pinged when it was not.
        err = HttpError(FakeResp(403), b"forbidden")
        client = SitemapsClient(submit_error=err)
        with self.assertRaises(gsc.AccessError):
            gsc.submit_sitemap(client, "s", SITEMAP_URL)

    def test_non_403_errors_still_propagate(self):
        err = HttpError(FakeResp(500), b"server error")
        client = SitemapsClient(submit_error=err)
        with self.assertRaises(HttpError):
            gsc.submit_sitemap(client, "s", SITEMAP_URL)


class GetSitemaps(unittest.TestCase):
    def test_parses_path_lastdownloaded_and_submitted_count(self):
        client = SitemapsClient(sitemaps=[{
            "path": SITEMAP_URL,
            "lastDownloaded": "2026-07-08T09:00:00.000Z",
            "isSitemapsIndex": True,
            "contents": [{"type": "web", "submitted": "65", "indexed": "60"}],
        }])
        result = gsc.get_sitemaps(client, "sc-domain:bessavagner.com")
        self.assertEqual(result[0]["path"], SITEMAP_URL)
        self.assertEqual(result[0]["lastDownloaded"], "2026-07-08T09:00:00.000Z")
        self.assertEqual(result[0]["submitted"], 65)  # API returns int64 as a string

    def test_multiple_content_types_sum_to_one_submitted_count(self):
        client = SitemapsClient(sitemaps=[{
            "path": SITEMAP_URL,
            "lastDownloaded": "2026-07-08T09:00:00.000Z",
            "contents": [
                {"type": "web", "submitted": "50", "indexed": "48"},
                {"type": "image", "submitted": "15", "indexed": "10"},
            ],
        }])
        result = gsc.get_sitemaps(client, "s")
        self.assertEqual(result[0]["submitted"], 65)

    def test_never_downloaded_sitemap_has_no_lastdownloaded_and_zero_submitted(self):
        # A sitemap just submitted but not yet crawled has no lastDownloaded
        # and no contents key at all — must not KeyError or fabricate a count.
        client = SitemapsClient(sitemaps=[{"path": SITEMAP_URL}])
        result = gsc.get_sitemaps(client, "s")
        self.assertEqual(result[0]["path"], SITEMAP_URL)
        self.assertEqual(result[0]["lastDownloaded"], "")
        self.assertEqual(result[0]["submitted"], 0)

    def test_calls_api_with_site(self):
        client = SitemapsClient(sitemaps=[])
        gsc.get_sitemaps(client, "sc-domain:bessavagner.com")
        self.assertEqual(client._sitemaps.last_list_kwargs["siteUrl"], "sc-domain:bessavagner.com")

    def test_no_sitemaps_returns_empty_list(self):
        self.assertEqual(gsc.get_sitemaps(SitemapsClient(sitemaps=[]), "s"), [])


class SitemapFreshness(unittest.TestCase):
    """The CI ping is `continue-on-error` with `exit 0` on every path and emits
    only `::warning::` — success and silent regression look identical. The
    report is where a stale sitemap becomes visible, and a stale one must never
    read as a healthy 0.
    """

    TODAY = date(2026, 8, 9)

    def test_days_since_download_is_a_bare_number_the_delta_engine_can_read(self):
        import history
        ms = gsc.sitemap_freshness_metrics(
            [{"path": SITEMAP_URL, "lastDownloaded": "2026-08-02T09:00:00.000Z",
              "submitted": 77}],
            today=self.TODAY,
        )
        by_name = {m.name: m.value for m in ms}
        self.assertEqual(by_name[f"{SITEMAP_URL} — days since last download"], "7")
        self.assertEqual(by_name[f"{SITEMAP_URL} — URLs submitted"], "77")
        for m in ms:
            self.assertEqual(m.source, "GSC")
            self.assertNotEqual(history.parse_numeric(m.value), "")

    def test_a_never_downloaded_sitemap_is_pending_not_zero_days(self):
        # "0 days since download" would read as PERFECTLY FRESH — the exact
        # inversion of the truth. Google has never fetched it.
        ms = gsc.sitemap_freshness_metrics(
            [{"path": SITEMAP_URL, "lastDownloaded": "", "submitted": 0}],
            today=self.TODAY,
        )
        days = [m for m in ms if m.name.endswith("days since last download")][0]
        self.assertEqual(days.value, "pending")
        self.assertNotEqual(days.value, "0")
        self.assertIn("never downloaded", days.note.lower())

    def test_a_never_downloaded_sitemap_reports_urls_submitted_as_pending_not_zero(self):
        # `submitted` is summed from GSC's `contents`, which Google only
        # populates once it actually processes the file. Before that, "0" is
        # not a measured empty sitemap — it is "nothing has been measured yet",
        # and must render the same way "pending" days does, not as a bare 0.
        ms = gsc.sitemap_freshness_metrics(
            [{"path": SITEMAP_URL, "lastDownloaded": "", "submitted": 0}],
            today=self.TODAY,
        )
        submitted = [m for m in ms if m.name.endswith("URLs submitted")][0]
        self.assertEqual(submitted.value, "pending")
        self.assertNotEqual(submitted.value, "0")
        self.assertTrue(submitted.note)
        self.assertIn("never", submitted.note.lower())
        self.assertIn("not", submitted.note.lower())

    def test_a_stale_sitemap_says_so_in_its_note(self):
        ms = gsc.sitemap_freshness_metrics(
            [{"path": SITEMAP_URL, "lastDownloaded": "2026-06-01T09:00:00.000Z",
              "submitted": 77}],
            today=self.TODAY,
        )
        days = [m for m in ms if m.name.endswith("days since last download")][0]
        self.assertEqual(days.value, "69")
        self.assertIn("stale", days.note.lower())

    def test_the_stale_boundary_at_exactly_14_days_is_not_yet_stale(self):
        # STALE_AFTER_DAYS = 14 and the note fires on `days > STALE_AFTER_DAYS`,
        # so day 14 itself must read as fresh (no stale note). Pin the exact
        # boundary so a future off-by-one (e.g. `>=`) turns this red instead
        # of silently suppressing a day's warning.
        self.assertEqual(gsc.STALE_AFTER_DAYS, 14)
        ms = gsc.sitemap_freshness_metrics(
            [{"path": SITEMAP_URL, "lastDownloaded": "2026-07-26T09:00:00.000Z",
              "submitted": 77}],
            today=self.TODAY,
        )
        days = [m for m in ms if m.name.endswith("days since last download")][0]
        self.assertEqual(days.value, "14")
        self.assertEqual(days.note, "")

    def test_the_stale_boundary_at_15_days_is_stale(self):
        ms = gsc.sitemap_freshness_metrics(
            [{"path": SITEMAP_URL, "lastDownloaded": "2026-07-25T09:00:00.000Z",
              "submitted": 77}],
            today=self.TODAY,
        )
        days = [m for m in ms if m.name.endswith("days since last download")][0]
        self.assertEqual(days.value, "15")
        self.assertIn("stale", days.note.lower())

    def test_no_registered_sitemap_is_pending_never_an_empty_section(self):
        # An empty section reads as "nothing to report". No sitemap registered
        # at all is the loudest possible finding.
        ms = gsc.sitemap_freshness_metrics([], today=self.TODAY)
        self.assertTrue(ms)
        self.assertTrue(all(m.value == "pending" for m in ms))
        self.assertIn("no sitemap is registered", ms[0].note.lower())

    def test_a_lastdownloaded_ahead_of_today_clamps_to_zero_not_negative(self):
        # lastDownloaded is UTC; `today` (date.today()) is local (UTC-3 here).
        # A sitemap Google fetched at 2026-07-14T01:00Z while the local date is
        # still 2026-07-13 must never render "-1 days" — a nonsense cell that
        # then deltas. Clamp at 0.
        ms = gsc.sitemap_freshness_metrics(
            [{"path": SITEMAP_URL, "lastDownloaded": "2026-07-14T01:00:00.000Z",
              "submitted": 77}],
            today=date(2026, 7, 13),
        )
        days = [m for m in ms if m.name.endswith("days since last download")][0]
        self.assertEqual(days.value, "0")
        self.assertNotIn("-", days.value)


class ScopeGuard(unittest.TestCase):
    """Least-privilege regression guard (binding constraint of this feature).

    The monthly report pipeline must keep read-only Search Console credentials
    forever. If someone later widens SCOPES to unlock a write call instead of
    adding a separate write path, this must fail loudly.
    """

    def test_read_scope_is_still_readonly_only(self):
        self.assertEqual(
            gsc.SCOPES, ["https://www.googleapis.com/auth/webmasters.readonly"]
        )

    def test_write_scope_is_not_the_readonly_scope(self):
        self.assertTrue(len(gsc.WRITE_SCOPES) > 0)
        for scope in gsc.WRITE_SCOPES:
            self.assertFalse(scope.endswith(".readonly"))
        self.assertIn("https://www.googleapis.com/auth/webmasters", gsc.WRITE_SCOPES)
