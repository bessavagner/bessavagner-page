import unittest

import history
import pinned


def page_row(path: str, impressions: int, clicks: int, ctr: float, position: float) -> dict:
    """A row exactly as the Search Analytics API returns it for dimension=page."""
    return {
        "keys": [f"https://bessavagner.com{path}"],
        "clicks": clicks,
        "impressions": impressions,
        "ctr": ctr,
        "position": position,
    }


REGWATCH_02 = "/building/regwatch/02-fetching-the-gazette-inlabs-ingestor/"
MD_NUMPY = "/blog/fast-molecular-dynamics-in-numpy/"
HOME = "/"


class ThePinnedListIsInCode(unittest.TestCase):
    """Anything that must survive lives in CODE — a list kept in the rendered
    .md is silently deleted by the next regeneration (report.ROLLING_READOUTS
    exists for exactly that reason).
    """

    def test_the_three_c3_targets_and_the_two_d_cluster_pages_are_pinned(self):
        for path in (
            REGWATCH_02,
            MD_NUMPY,
            HOME,
            "/blog/pulling-structured-data-from-unstructured-documents/",  # D1
            "/blog/beating-browser-fingerprinting/",                       # D2
        ):
            self.assertIn(path, pinned.PINNED_PATHS)


class ByNameNotByRank(unittest.TestCase):
    """The defect this module exists to fix: a page that falls out of the top-10
    vanishes from history that month, so the series goes blank precisely when
    the page gets worse.
    """

    def test_a_pinned_page_emits_rows_even_when_it_is_not_in_the_top_10(self):
        # Twelve higher-impression pages ahead of it; a top-10 slice would drop it.
        rows = [page_row(f"/blog/filler-{i}/", 500 + i, 5, 0.01, 3.0) for i in range(12)]
        rows.append(page_row(REGWATCH_02, 41, 0, 0.0, 3.9))
        ms = pinned.pinned_metrics(rows, paths=(REGWATCH_02,))
        by_name = {m.name: m.value for m in ms}
        self.assertEqual(by_name[f"{REGWATCH_02} — impressions"], "41")
        self.assertEqual(by_name[f"{REGWATCH_02} — position"], "3.9")

    def test_every_pinned_page_emits_one_metric_per_measure(self):
        rows = [page_row(HOME, 30, 0, 0.0, 7.8)]
        ms = pinned.pinned_metrics(rows, paths=(HOME, MD_NUMPY))
        self.assertEqual(len(ms), 2 * len(pinned.MEASURES))
        self.assertTrue(all(m.source == "GSC" for m in ms))

    def test_values_are_formatted_one_measure_per_row(self):
        rows = [page_row(MD_NUMPY, 32, 0, 0.0, 5.8)]
        by_name = {m.name: m.value for m in pinned.pinned_metrics(rows, paths=(MD_NUMPY,))}
        self.assertEqual(by_name[f"{MD_NUMPY} — impressions"], "32")
        self.assertEqual(by_name[f"{MD_NUMPY} — clicks"], "0")
        self.assertEqual(by_name[f"{MD_NUMPY} — CTR"], "0.00%")
        self.assertEqual(by_name[f"{MD_NUMPY} — position"], "5.8")


class AnAbsentPageIsPendingNeverZero(unittest.TestCase):
    """`inspect_urls` already sets this idiom: an absence of measurement is not
    a measured 0. A pinned page GSC returns nothing for did not get zero
    impressions — we do not know what it got.
    """

    def test_a_pinned_page_absent_from_the_response_is_pending_with_a_reason(self):
        ms = pinned.pinned_metrics([], paths=(HOME,))
        self.assertEqual(len(ms), len(pinned.MEASURES))
        for m in ms:
            self.assertEqual(m.value, "pending")
            self.assertNotEqual(m.value, "0")
            self.assertIn("not a measured 0", m.note.lower())

    def test_an_absent_page_does_not_suppress_the_pages_that_are_present(self):
        rows = [page_row(HOME, 30, 1, 0.033, 7.8)]
        by_name = {m.name: m.value for m in pinned.pinned_metrics(rows, paths=(HOME, MD_NUMPY))}
        self.assertEqual(by_name[f"{HOME} — impressions"], "30")
        self.assertEqual(by_name[f"{MD_NUMPY} — impressions"], "pending")

    def test_a_slashless_homepage_url_still_matches_the_pinned_homepage(self):
        # If GSC ever returns the homepage key WITHOUT its trailing slash
        # ("https://bessavagner.com"), splitting on SITE_HOST leaves an empty
        # remainder. The old `or url` fallback then returned the WHOLE url as
        # the path, which never matches "/" in PINNED_PATHS — so the homepage
        # would render pending every month, forever, with a note claiming GSC
        # returned no row. It must normalise to "/" instead.
        rows = [{
            "keys": ["https://bessavagner.com"],
            "clicks": 2, "impressions": 40, "ctr": 0.05, "position": 6.1,
        }]
        by_name = {m.name: m.value for m in pinned.pinned_metrics(rows, paths=(HOME,))}
        self.assertEqual(by_name[f"{HOME} — impressions"], "40")
        self.assertNotEqual(by_name[f"{HOME} — impressions"], "pending")


class TheRowsMustBeReadableByTheDeltaEngine(unittest.TestCase):
    """STABLE_KEY_SECTIONS membership is necessary but NOT sufficient:
    delta_for also refuses on a non-numeric value, and history.parse_numeric
    returns "" for GSC's composite "179 impr · 1 clicks · …" string. Emit a
    composite into a stable section and the delta is refused forever — silently.
    """

    def test_every_measured_value_parses_to_a_number(self):
        rows = [page_row(MD_NUMPY, 32, 1, 0.031, 5.8)]
        for m in pinned.pinned_metrics(rows, paths=(MD_NUMPY,)):
            self.assertNotEqual(history.parse_numeric(m.value), "",
                                f"{m.name} is not delta-readable: {m.value!r}")

    def test_a_pending_value_parses_to_empty_never_to_zero(self):
        for m in pinned.pinned_metrics([], paths=(MD_NUMPY,)):
            self.assertEqual(history.parse_numeric(m.value), "")

    def test_the_position_row_warns_that_a_positive_delta_is_worse(self):
        rows = [page_row(MD_NUMPY, 32, 0, 0.0, 5.8)]
        pos = [m for m in pinned.pinned_metrics(rows, paths=(MD_NUMPY,))
               if m.name.endswith("position")][0]
        self.assertIn("lower is better", pos.note.lower())

    def test_the_ctr_row_says_its_delta_is_in_percentage_points(self):
        rows = [page_row(MD_NUMPY, 32, 1, 0.031, 5.8)]
        ctr = [m for m in pinned.pinned_metrics(rows, paths=(MD_NUMPY,))
               if m.name.endswith("CTR")][0]
        self.assertIn("percentage point", ctr.note.lower())


if __name__ == "__main__":
    unittest.main()
