import unittest
from datetime import date

import gsc
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
