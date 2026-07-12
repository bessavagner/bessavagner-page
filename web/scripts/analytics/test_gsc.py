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
        return FakeQuery(self.rows_by_dim.get(key, []))


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
