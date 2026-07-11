import unittest
from datetime import date

import window


class MonthWindow(unittest.TestCase):
    def test_august(self):
        w = window.month_window("2026-08")
        self.assertEqual(w.start, date(2026, 8, 1))
        self.assertEqual(w.end, date(2026, 8, 31))

    def test_february_non_leap(self):
        w = window.month_window("2026-02")
        self.assertEqual(w.end, date(2026, 2, 28))


class ComparisonWindow(unittest.TestCase):
    def test_month_fully_before_ga4_is_orphaned(self):
        w = window.month_window("2026-05")  # GA4 installed 2026-06-28
        self.assertIsNone(window.comparison_window(w, date(2026, 6, 28)))
        self.assertFalse(window.is_reconcilable(w, date(2026, 6, 28)))

    def test_month_after_ga4_is_full(self):
        w = window.month_window("2026-08")
        cmp = window.comparison_window(w, date(2026, 6, 28))
        self.assertEqual(cmp.start, date(2026, 8, 1))
        self.assertEqual(cmp.end, date(2026, 8, 31))

    def test_month_straddling_ga4_is_clamped(self):
        w = window.month_window("2026-06")
        cmp = window.comparison_window(w, date(2026, 6, 28))
        self.assertEqual(cmp.start, date(2026, 6, 28))  # clamped to install date
        self.assertEqual(cmp.end, date(2026, 6, 30))
        self.assertTrue(window.is_reconcilable(w, date(2026, 6, 28)))
