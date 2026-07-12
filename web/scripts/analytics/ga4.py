"""GA4 Data API pull (read-only). ctx 05 §4: GA4 is the channel/conversion truth.

The Data API dimension for utm_content is `sessionManualAdContent`; utm_campaign
is `sessionCampaignName`. Metrics: engagedSessions, screenPageViewsPerSession,
eventCount. Runs against property 543524687 with the ga4-venv service account.
"""
from __future__ import annotations

import os

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Filter,
    FilterExpression,
    FilterExpressionList,
    Metric as GaMetric,
    RunReportRequest,
)

from report import Metric
from window import Window


def property_id() -> str:
    return os.environ.get("GA4_PROPERTY_ID", "543524687")


def build_client() -> BetaAnalyticsDataClient:
    return BetaAnalyticsDataClient()


def _date_range(w: Window) -> DateRange:
    return DateRange(start_date=w.start.isoformat(), end_date=w.end.isoformat())


def format_pages_per_session(value: str) -> str:
    """Round the raw GA4 screenPageViewsPerSession ratio to 2 decimals.

    Pure and testable: GA4 returns full-precision floats like
    "1.6129032258064515"; the report shows "1.61".
    """
    return f"{float(value):.2f}"


def fetch_channel_engagement(client, property_id: str, w: Window) -> list[Metric]:
    req = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[_date_range(w)],
        dimensions=[Dimension(name="sessionDefaultChannelGroup")],
        metrics=[
            GaMetric(name="sessions"),
            GaMetric(name="engagedSessions"),
            GaMetric(name="screenPageViewsPerSession"),
        ],
    )
    resp = client.run_report(req)
    out: list[Metric] = []
    for row in resp.rows:
        channel = row.dimension_values[0].value
        sessions, engaged, pps = (v.value for v in row.metric_values)
        out.append(Metric(f"{channel} — sessions", sessions, "GA4"))
        out.append(Metric(f"{channel} — engaged sessions", engaged, "GA4"))
        out.append(Metric(
            f"{channel} — pages/session", format_pages_per_session(pps), "GA4",
            note="goal > 2.0",
        ))
    return out


def split_reported_and_missing(
    seen: dict[str, str], event_names: list[str]
) -> tuple[list[Metric], list[str]]:
    """Decide, per requested event, whether GA4 actually reported it.

    Pure and testable (no API client needed): GA4 returns NO ROW for an event
    it has no data for — that absence must never be turned into a measured
    "0" (ctx 05 §1: flag, don't zero-fill). An event present in `seen` becomes
    a real Metric; an event absent from `seen` is reported as MISSING and is
    NEVER emitted as a Metric here — the caller decides how to flag it.
    """
    reported = [Metric(n, seen[n], "GA4") for n in event_names if n in seen]
    missing = [n for n in event_names if n not in seen]
    return reported, missing


def fetch_key_event_counts(
    client, property_id: str, w: Window, event_names: list[str]
) -> tuple[list[Metric], list[str]]:
    """Return (reported, missing) — see split_reported_and_missing.

    The API call stays thin; all the "is this a real 0 or an absence"
    decision logic lives in the pure helper above.
    """
    name_filter = FilterExpression(
        or_group=FilterExpressionList(
            expressions=[
                FilterExpression(
                    filter=Filter(
                        field_name="eventName",
                        string_filter=Filter.StringFilter(value=n),
                    )
                )
                for n in event_names
            ]
        )
    )
    req = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[_date_range(w)],
        dimensions=[Dimension(name="eventName")],
        metrics=[GaMetric(name="eventCount")],
        dimension_filter=name_filter,
    )
    resp = client.run_report(req)
    seen = {row.dimension_values[0].value: row.metric_values[0].value for row in resp.rows}
    return split_reported_and_missing(seen, event_names)


FILE_DOWNLOAD_EVENT = "file_download"
FILE_DOWNLOAD_NOTE = (
    "GA4's nearest auto-tracked download signal (CV/PDF); not the custom "
    "`cv_download` event"
)


def fetch_file_download_proxy(client, property_id: str, w: Window) -> Metric | None:
    """GA4's enhanced-measurement `file_download` event.

    Surfaced as the nearest auto-tracked proxy for the custom `cv_download`
    event, which is NOT instrumented in GA4 (only Umami captures it). Returns
    None when GA4 reported nothing for `file_download` either — never "0".
    """
    req = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[_date_range(w)],
        dimensions=[Dimension(name="eventName")],
        metrics=[GaMetric(name="eventCount")],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="eventName",
                string_filter=Filter.StringFilter(value=FILE_DOWNLOAD_EVENT),
            )
        ),
    )
    resp = client.run_report(req)
    seen = {row.dimension_values[0].value: row.metric_values[0].value for row in resp.rows}
    count = seen.get(FILE_DOWNLOAD_EVENT)
    if count is None:
        return None
    return Metric(
        f"{FILE_DOWNLOAD_EVENT} (enhanced-measurement)", count, "GA4",
        note=FILE_DOWNLOAD_NOTE,
    )


def fetch_utm_content(client, property_id: str, w: Window) -> list[dict[str, str]]:
    req = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[_date_range(w)],
        dimensions=[
            Dimension(name="sessionCampaignName"),
            Dimension(name="sessionManualAdContent"),
        ],
        metrics=[GaMetric(name="sessions")],
    )
    resp = client.run_report(req)
    return [
        {
            "campaign": row.dimension_values[0].value,
            "utm_content": row.dimension_values[1].value,
            "sessions": row.metric_values[0].value,
        }
        for row in resp.rows
    ]
