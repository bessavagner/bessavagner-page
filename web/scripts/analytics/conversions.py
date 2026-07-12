"""Assemble the Conversions section: exactly one authoritative figure per action.

Two rules live here, and they live here because they cannot be tested inside
monthly_report.main():

A3 — CONDITIONAL PROXY RETIREMENT. GA4's enhanced-measurement `file_download`
exists in this report only as a stand-in for a `cv_download` GA4 never reported.
The instant GA4 reports a real `cv_download`, the proxy falls away — two numbers
for one action is the ambiguity this sprint exists to kill. It is retired
CONDITIONALLY, never deleted: in a month where GA4 reports no `cv_download` (at
~4 events/month minus ad-blocker attrition, a likely month), the proxy is the
only download signal there is.

NO SILENT ZERO. GA4 returns no row for an event it never received. That absence
is flagged with a stated reason and its Umami raw count — never rendered as a
measured "0" (ctx 05 section 1). Marking the key events (A1) is precisely the
change that would tempt someone to zero-fill.
"""
from __future__ import annotations

from report import Metric

CV_DOWNLOAD = "cv_download"


def build_conversions(
    reported: list[Metric],
    missing: list[str],
    proxy: Metric | None,
    umami_counts: dict[str, int],
) -> tuple[list[Metric], list[Metric]]:
    """-> (conversions, flagged). Pure — no API client, no network.

    `reported` / `missing` come from ga4.split_reported_and_missing, which has
    already made the "is this a real 0 or an absence" call. `proxy` is None when
    GA4 reported nothing for file_download either.
    """
    real_names = {m.name for m in reported}
    show_proxy = proxy is not None and CV_DOWNLOAD not in real_names

    conversions = list(reported)
    if show_proxy:
        conversions.append(proxy)

    flagged: list[Metric] = []
    for name in missing:
        raw = umami_counts.get(name)
        if name == CV_DOWNLOAD and show_proxy:
            note = (
                f"GA4 received no {name} in this window (Umami raw {raw}, see Reach) "
                f"— not a measured 0. Nearest GA4 signal: enhanced-measurement "
                f"`file_download` = {proxy.value}, shown above as the stand-in."
            )
        else:
            note = (
                f"GA4 received no {name} in this window (Umami raw {raw}, see Reach) "
                f"— not a measured 0. The event is verified firing (A0); GA4 simply "
                f"has no row for it here."
            )
        flagged.append(Metric(name, "no GA4 events in window", "GA4", note=note))

    return conversions, flagged
