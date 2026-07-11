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
        out.append(Metric(f"{channel} — pages/session", pps, "GA4", note="goal > 2.0"))
    return out


def fetch_key_event_counts(client, property_id: str, w: Window, event_names: list[str]) -> list[Metric]:
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
    # A requested event with no GA4 rows is returned as "0" here; Task 6 decides
    # whether that 0 is real (GA4-era) or must be flagged as orphaned by the window.
    return [Metric(n, seen.get(n, "0"), "GA4") for n in event_names]


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
