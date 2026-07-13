import unittest

import indexation
from report import Metric


def idx(name: str, value: str, note: str = "") -> Metric:
    """One row as gsc.inspect_urls() emits it."""
    return Metric(name, value, "GSC", note=note)


class ThreeBucketsNeverTwo(unittest.TestCase):
    """`pending` and `not indexed` are OPPOSITE conclusions. One sends you
    rewriting a page that is perfectly fine; the other is a quota error. A
    verdict that folds pending into not-indexed is worse than the buried table
    it replaces — it is the silent-zero bug wearing a third hat.
    """

    def _by_name(self, rows):
        return {m.name: m.value for m in indexation.verdict_metrics(rows)}

    def test_pending_is_never_counted_as_not_indexed(self):
        counts = self._by_name([
            idx("/blog/a/", "Submitted and indexed"),
            idx("/blog/b/", "pending", note="inspection failed (429) — NOT a 'not indexed' verdict; re-run"),
            idx("/blog/c/", "Crawled - currently not indexed"),
        ])
        self.assertEqual(counts["Posts indexed"], "1")
        self.assertEqual(counts["Posts not indexed"], "1")     # NOT 2
        self.assertEqual(counts["Posts pending inspection"], "1")

    def test_indexed_not_submitted_in_sitemap_counts_as_indexed(self):
        # The trap in the string match: this state CONTAINS "not submitted",
        # but it does not contain "not indexed" — the page IS in the index.
        counts = self._by_name([idx("/blog/a/", "Indexed, not submitted in sitemap")])
        self.assertEqual(counts["Posts indexed"], "1")
        self.assertEqual(counts["Posts not indexed"], "0")

    def test_url_unknown_to_google_counts_as_not_indexed(self):
        # The state of C1's five URLs. Google has never seen it: not indexed.
        counts = self._by_name([idx("/building/regwatch/03-the-daily-run-made-real/",
                                    "URL is unknown to Google")])
        self.assertEqual(counts["Posts not indexed"], "1")
        self.assertEqual(counts["Posts indexed"], "0")

    def test_discovered_currently_not_indexed_counts_as_not_indexed(self):
        counts = self._by_name([idx("/blog/a/", "Discovered - currently not indexed")])
        self.assertEqual(counts["Posts not indexed"], "1")

    def test_the_three_buckets_always_sum_to_the_row_count(self):
        rows = [
            idx("/blog/a/", "Submitted and indexed"),
            idx("/blog/b/", "pending"),
            idx("/blog/c/", "URL is unknown to Google"),
            idx("/blog/d/", "Indexed, not submitted in sitemap"),
            idx("/blog/e/", "Excluded by 'noindex' tag"),
        ]
        counts = self._by_name(rows)
        self.assertEqual(sum(int(v) for v in counts.values()), len(rows))


class TheShapeOfTheVerdict(unittest.TestCase):
    def test_exactly_three_metrics_in_a_fixed_order_all_sourced_gsc(self):
        ms = indexation.verdict_metrics([idx("/blog/a/", "Submitted and indexed")])
        self.assertEqual(
            [m.name for m in ms],
            ["Posts indexed", "Posts not indexed", "Posts pending inspection"],
        )
        self.assertTrue(all(m.source == "GSC" for m in ms))

    def test_every_value_is_bare_numeric_so_the_delta_engine_can_read_it(self):
        # STABLE_KEY_SECTIONS membership is necessary but NOT sufficient:
        # deltas.delta_for also refuses on a non-numeric value, and
        # history.parse_numeric returns "" for anything that is not a number.
        import history
        for m in indexation.verdict_metrics([idx("/blog/a/", "Submitted and indexed")]):
            self.assertNotEqual(history.parse_numeric(m.value), "",
                                f"{m.name} is not delta-readable: {m.value!r}")

    def test_no_posts_published_is_pending_not_a_measured_zero(self):
        # The GSC lane RAN, but there was nothing to inspect: no posts were
        # published this month. "0" is numeric and delta-eligible — the delta
        # engine would compute a real percentage against last month's real
        # count and fabricate a "-100%" deindexation out of an absence of
        # measurement. So this renders `pending`, not `"0"`, on all three
        # buckets.
        ms = indexation.verdict_metrics([])
        self.assertEqual([m.value for m in ms], [indexation.PENDING] * 3)
        self.assertFalse(any(m.value == "0" for m in ms))
        for m in ms:
            self.assertIn("not a measured 0", m.note.lower())


class TheLaneThatNeverRan(unittest.TestCase):
    """--skip-gsc, or GSC returning no data for the month. A 0/0/0 count on a
    lane that never ran is a fabricated zero wearing a verdict's clothes.
    """

    def test_an_unmeasured_lane_renders_pending_never_zero(self):
        ms = indexation.unmeasured_verdict("the GSC lane was skipped")
        self.assertEqual([m.value for m in ms], ["pending", "pending", "pending"])
        self.assertFalse(any(m.value == "0" for m in ms))
        for m in ms:
            self.assertIn("the GSC lane was skipped", m.note)
            self.assertIn("not a measured zero", m.note.lower())

    def test_it_keeps_the_same_three_names_as_the_measured_verdict(self):
        self.assertEqual(
            [m.name for m in indexation.unmeasured_verdict("no GSC data")],
            [m.name for m in indexation.verdict_metrics([])],
        )


if __name__ == "__main__":
    unittest.main()
