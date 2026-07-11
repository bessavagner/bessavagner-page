import os
import tempfile
import unittest
from datetime import date

import umami


class LoadWebsiteEvents(unittest.TestCase):
    def _write(self, dirpath, text):
        with open(os.path.join(dirpath, "website_event.csv"), "w", encoding="utf-8") as f:
            f.write(text)

    def test_missing_column_fails_loudly(self):
        with tempfile.TemporaryDirectory() as d:
            self._write(d, "event_name,created_at\ncv_download,2026-08-01T10:00:00Z\n")
            with self.assertRaises(umami.SchemaError):
                umami.load_website_events(d)

    def test_loads_rows(self):
        with tempfile.TemporaryDirectory() as d:
            self._write(
                d,
                "event_type,event_name,created_at\n"
                "2,cv_download,2026-08-01T10:00:00Z\n"
                "1,,2026-08-01T10:00:01Z\n",
            )
            rows = umami.load_website_events(d)
            self.assertEqual(len(rows), 2)


class CountEvent(unittest.TestCase):
    ROWS = [
        {"event_type": "2", "event_name": "cv_download", "created_at": "2026-08-01T10:00:00Z"},
        {"event_type": "2", "event_name": "cv-download", "created_at": "2026-08-15T09:00:00Z"},
        {"event_type": "2", "event_name": "cv_download", "created_at": "2026-09-01T09:00:00Z"},
        {"event_type": "1", "event_name": "", "created_at": "2026-08-02T09:00:00Z"},
        {"event_type": "2", "event_name": "whatsapp_click", "created_at": "2026-08-03T09:00:00Z"},
    ]

    def test_counts_name_and_legacy_alias_in_window(self):
        n = umami.count_event(
            self.ROWS, ["cv_download", "cv-download"], date(2026, 8, 1), date(2026, 8, 31)
        )
        self.assertEqual(n, 2)  # snake + hyphen inside August; the Sept row excluded

    def test_excludes_other_events(self):
        # counting cv_download must not pick up the whatsapp_click row in the same window
        n = umami.count_event(
            self.ROWS, ["cv_download", "cv-download"], date(2026, 8, 1), date(2026, 8, 31)
        )
        self.assertEqual(n, 2)  # only the two cv_download rows — not whatsapp_click or the blank
        # requesting whatsapp_click returns exactly its own single row
        self.assertEqual(
            umami.count_event(self.ROWS, ["whatsapp_click"], date(2026, 8, 1), date(2026, 8, 31)),
            1,
        )
