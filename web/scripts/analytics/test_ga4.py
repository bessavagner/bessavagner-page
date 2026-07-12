import unittest
from datetime import date

import ga4
from report import Metric
from window import Window


class SplitReportedAndMissing(unittest.TestCase):
    """The cardinal-rule regression guard: GA4 returns NO ROW for an event it
    has no data for. That absence must never be turned into a measured "0"
    (ctx 05 §1: flag, don't zero-fill).
    """

    def test_event_ga4_reported_comes_back_as_a_real_metric(self):
        reported, missing = ga4.split_reported_and_missing(
            {"cv_download": "3"}, ["cv_download"]
        )
        self.assertEqual(reported, [Metric("cv_download", "3", "GA4")])
        self.assertEqual(missing, [])

    def test_event_ga4_reported_nothing_for_is_missing_not_zero(self):
        reported, missing = ga4.split_reported_and_missing({}, ["cv_download"])
        self.assertEqual(reported, [])
        self.assertEqual(missing, ["cv_download"])
        # The unmissable regression guard: no Metric anywhere in `reported`
        # may carry value "0" for an event GA4 never reported.
        self.assertFalse(any(m.value == "0" for m in reported))

    def test_mixed_reported_and_missing_never_fabricates_a_zero(self):
        reported, missing = ga4.split_reported_and_missing(
            {"whatsapp_click": "1"},
            ["whatsapp_click", "generate_lead", "newsletter_signup"],
        )
        self.assertEqual(reported, [Metric("whatsapp_click", "1", "GA4")])
        self.assertEqual(missing, ["generate_lead", "newsletter_signup"])
        self.assertFalse(any(m.value == "0" for m in reported))
        # And the missing events must never appear as reported Metrics either.
        reported_names = {m.name for m in reported}
        self.assertNotIn("generate_lead", reported_names)
        self.assertNotIn("newsletter_signup", reported_names)

    def test_all_reported_yields_no_missing(self):
        reported, missing = ga4.split_reported_and_missing(
            {"a": "5", "b": "0"}, ["a", "b"]
        )
        # Note: "0" is fine here — GA4 DID report a row for "b" with count 0.
        # That is a real measured zero, not an absence, so it is a legitimate
        # Metric — the cardinal rule only forbids fabricating "0" for an
        # event GA4 never reported at all.
        self.assertEqual(reported, [Metric("a", "5", "GA4"), Metric("b", "0", "GA4")])
        self.assertEqual(missing, [])


class FormatPagesPerSession(unittest.TestCase):
    def test_rounds_to_two_decimals(self):
        self.assertEqual(ga4.format_pages_per_session(str(50 / 31)), "1.61")

    def test_whole_number_gets_trailing_zeros(self):
        self.assertEqual(ga4.format_pages_per_session(str(4 / 1)), "4.00")

    def test_rounds_up_correctly(self):
        # 50/31 = 1.6129032258064515 -> matches the owner's hand-corrected
        # report value of 1.63 for a different channel's ratio.
        self.assertEqual(ga4.format_pages_per_session("1.6291666666666667"), "1.63")


class _Value:
    def __init__(self, value):
        self.value = value


class _Row:
    def __init__(self, dims, mets):
        self.dimension_values = [_Value(d) for d in dims]
        self.metric_values = [_Value(m) for m in mets]


class _Resp:
    def __init__(self, rows):
        self.rows = rows


class FakeGa4Client:
    """Stands in for BetaAnalyticsDataClient — no network, no credentials."""

    def __init__(self, rows):
        self._rows = rows

    def run_report(self, req):
        return _Resp(self._rows)


JULY = Window(date(2026, 7, 1), date(2026, 7, 11))


class FetchChannelEngagement(unittest.TestCase):
    def test_pages_per_session_is_rounded_in_the_emitted_metric(self):
        client = FakeGa4Client([
            _Row(["Direct"], ["57", "10", "1.5087719298245615"]),
        ])
        metrics = ga4.fetch_channel_engagement(client, "123", JULY)
        by_name = {m.name: m for m in metrics}
        self.assertEqual(by_name["Direct — pages/session"].value, "1.51")
        self.assertEqual(by_name["Direct — pages/session"].note, "goal > 2.0")
        self.assertEqual(by_name["Direct — sessions"].value, "57")


class FetchKeyEventCounts(unittest.TestCase):
    def test_delegates_to_split_reported_and_missing(self):
        client = FakeGa4Client([_Row(["whatsapp_click"], ["1"])])
        reported, missing = ga4.fetch_key_event_counts(
            client, "123", JULY, ["whatsapp_click", "cv_download"]
        )
        self.assertEqual(reported, [Metric("whatsapp_click", "1", "GA4")])
        self.assertEqual(missing, ["cv_download"])

    def test_no_rows_at_all_yields_everything_missing_never_zero(self):
        client = FakeGa4Client([])
        reported, missing = ga4.fetch_key_event_counts(
            client, "123", JULY, ["cv_download", "generate_lead"]
        )
        self.assertEqual(reported, [])
        self.assertEqual(missing, ["cv_download", "generate_lead"])


class FetchFileDownloadProxy(unittest.TestCase):
    def test_present_row_is_returned_as_a_labelled_ga4_metric(self):
        client = FakeGa4Client([_Row(["file_download"], ["3"])])
        m = ga4.fetch_file_download_proxy(client, "123", JULY)
        self.assertIsNotNone(m)
        self.assertEqual(m.value, "3")
        self.assertEqual(m.source, "GA4")
        self.assertIn("not the custom", m.note)

    def test_no_row_returns_none_not_zero(self):
        client = FakeGa4Client([])
        self.assertIsNone(ga4.fetch_file_download_proxy(client, "123", JULY))


if __name__ == "__main__":
    unittest.main()
