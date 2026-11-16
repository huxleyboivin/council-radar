"""Render a weekly issue (Markdown, which Buttondown sends natively) from findings."""
from __future__ import annotations

from datetime import date

SECTIONS = [
    ("support_granted", "Support granted"),
    ("support_denied", "Support refused, deferred or acknowledgement-only"),
    ("support_request", "New support requests"),
    ("policy_protocol", "New council protocols and criteria"),
    ("zoning_bylaw", "Zoning, official plan and by-law changes"),
    ("delegation", "Early signals: delegations and presentations"),
    ("other_relevant", "Also on the radar"),
]
STATUS_LABEL = {"decided": "Decided", "recommended": "Staff recommendation", "on_agenda": "On agenda",
                "presented": "Presented", "information": "For information"}


def _get(f, k):
    try:
        return f[k]
    except (KeyError, IndexError):
        return None


def render(findings, feed_title: str, issue_date: date | None = None, intro: str = "",
           period_label: str = "this week") -> tuple[str, str]:
    issue_date = issue_date or date.today()
    subject = f"{feed_title} | week of {issue_date:%B %-d, %Y}"
    lines = [f"# {feed_title}", f"*Week of {issue_date:%B %-d, %Y}*", ""]
    if intro:
        lines += [intro, ""]
    munis = sorted({_get(f, "municipality") for f in findings if _get(f, "municipality")})
    lines += [f"**{len(findings)} items from {len(munis)} municipalities {period_label}.**", ""]
    if not findings:
        lines += ["No new council items matched this feed this week. We checked the published agendas "
                  "and minutes of every monitored council.", ""]
    for key, label in SECTIONS:
        group = [f for f in findings if _get(f, "category") == key]
        if not group:
            continue
        lines += [f"## {label}", ""]
        for f in group:
            bits = [b for b in (_get(f, "technology"),
                                f"{_get(f, 'capacity_mw'):g} MW" if _get(f, "capacity_mw") else None,
                                _get(f, "proponent")) if b]
            lines.append(f"### {_get(f, 'municipality')}: {_get(f, 'headline')}")
            meta = f"{STATUS_LABEL.get(_get(f, 'status'), 'Update')} · {_get(f, 'meeting_name') or 'Council'}"
            if _get(f, "meeting_date"):
                meta += f" · {_get(f, 'meeting_date')}"
            if bits:
                meta += " · " + " · ".join(bits)
            lines += [f"*{meta}*", "", _get(f, "summary") or ""]
            if _get(f, "evidence"):
                lines += ["", f"> \"{_get(f, 'evidence')}\""]
            if _get(f, "source_url"):
                lines += ["", f"[Read the source document]({_get(f, 'source_url')})"]
            lines.append("")
    lines += ["---",
              "*Council Radar reads public council and committee documents with AI and summarizes "
              "them. Always confirm details in the linked source before relying on them.*"]
    return subject, "\n".join(lines)
