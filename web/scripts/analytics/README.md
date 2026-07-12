# Monthly analytics merge (Umami CSV + GA4 Data API + Search Console)

One command merges the two analytics stacks into a single monthly Markdown
report. Run it from the shared `~/.config/claude-seo/ga4-venv` (Python 3.12,
already has `google-analytics-data`). Read-only against GA4 property 543524687.

## Trust which tool (ctx 05 §4)
- **Umami = reach truth:** pageviews, visitors, raw event counts.
- **GA4 = channel/conversion truth:** acquisition channels, attribution, key events.
- **GSC = pre-click/demand truth:** impressions, queries, position, index coverage —
  **Google organic only** (blind to LinkedIn, currently most of the traffic).
- **Never average them.** Three instruments, three lanes. Every figure names its source.

## GSC notes
- Data lags ~2-3 days. The report detects the range it *actually* covers and says so;
  it never claims a full month it did not measure.
- Google withholds rare queries for privacy, so query rows never sum to the totals row.
- Average position is impression-weighted and unstable at low volume.
- A failed URL inspection reports `pending`, never `not indexed` — opposite conclusions.
- `--skip-gsc` runs the merge without Search Console (offline / no credentials).

## Run
```
# 1. Pull the Umami Cloud export (gzip'd CSV) and unpack it somewhere, e.g. /tmp/umami-2026-08/
#    You need at least website_event.csv (session.csv / event_data.csv optional).
# 2. Activate the venv and run:
source ~/.config/claude-seo/ga4-venv/bin/activate
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json   # or ADC
cd web/scripts/analytics
python monthly_report.py --umami-dir /tmp/umami-2026-08 --month 2026-08 --ga4-start 2026-06-28
# → writes docs/.ai/reports/analytics/2026-08.md
```

## Tests
```
cd web/scripts/analytics
python -m unittest discover -s . -p 'test_*.py' -v
```
