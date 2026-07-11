# Monthly analytics merge (Umami CSV + GA4 Data API)

One command merges the two analytics stacks into a single monthly Markdown
report. Run it from the shared `~/.config/claude-seo/ga4-venv` (Python 3.12,
already has `google-analytics-data`). Read-only against GA4 property 543524687.

## Trust which tool (ctx 05 §4)
- **Umami = reach truth:** pageviews, visitors, raw event counts.
- **GA4 = channel/conversion truth:** acquisition channels, attribution, key events.
- **Never average the two.** Every figure in the report names its source tool.

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
