"""The AI read: turn prefiltered agenda text into structured findings for one feed."""
from __future__ import annotations

import json
import re

from . import config
from .prefilter import Feed

SYSTEM = """You read Ontario municipal council and committee documents (agendas, staff reports,
minutes, by-laws) for a paid alert service. Readers act on what you report, so accuracy
matters more than coverage: report only what the text actually says, never infer a vote
outcome that is not stated, and say "proposed", "recommended" or "on agenda" when a
decision has not been made yet."""

PROMPT = """Feed: {title}
Readers: {audience}

Document: {doc_title}
Municipality: {municipality}
Meeting: {meeting_name} on {meeting_date}
Source URL: {url}

Excerpts (keyword-matched passages; "..." separates them):
<excerpts>
{text}
</excerpts>

Return a JSON array (no prose). One object per distinct item that matters to these readers.
Return [] if nothing does (passing mentions, boilerplate, unrelated uses of a keyword).
Each object:
{{
  "category": one of {categories},
  "headline": "max 12 words, factual",
  "project": "project name or address, or null",
  "proponent": "company, or null",
  "technology": "e.g. BESS, solar, wind, gas, hydrogen, LDES, or null",
  "capacity_mw": number or null,
  "status": "decided | recommended | on_agenda | presented | information",
  "summary": "1-3 sentences: what happened or is proposed, and what it means for a developer",
  "evidence": "a short exact quote from the excerpts (max 30 words) that supports the summary",
  "confidence": 0.0-1.0
}}"""


def _client():
    import anthropic
    return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY or None)


def parse_json_array(text: str) -> list[dict]:
    text = text.strip()
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    return [d for d in data if isinstance(d, dict)]


def clean(item: dict, feed: Feed) -> dict | None:
    cat = item.get("category")
    if cat not in feed.categories:
        cat = "other_relevant" if "other_relevant" in feed.categories else None
    if not cat or not item.get("headline") or not item.get("summary"):
        return None
    try:
        mw = float(item["capacity_mw"]) if item.get("capacity_mw") not in (None, "") else None
    except (TypeError, ValueError):
        mw = None
    try:
        conf = max(0.0, min(1.0, float(item.get("confidence", 0.7))))
    except (TypeError, ValueError):
        conf = 0.7
    ev = " ".join(str(item.get("evidence") or "").split()[:30])
    return {
        "category": cat,
        "headline": str(item["headline"]).strip()[:140],
        "project": item.get("project") or None,
        "proponent": item.get("proponent") or None,
        "technology": item.get("technology") or None,
        "capacity_mw": mw,
        "status": item.get("status") or "information",
        "summary": str(item["summary"]).strip()[:800],
        "evidence": ev,
        "confidence": conf,
    }


def read(feed: Feed, text: str, meta: dict, client=None) -> list[dict]:
    client = client or _client()
    msg = client.messages.create(
        model=config.MODEL,
        max_tokens=2000,
        system=SYSTEM,
        messages=[{"role": "user", "content": PROMPT.format(
            title=feed.title, audience=feed.audience, categories=feed.categories, text=text, **meta)}],
    )
    out_text = "".join(getattr(b, "text", "") for b in msg.content)
    results = []
    for item in parse_json_array(out_text):
        c = clean(item, feed)
        if c:
            results.append(c)
    return results
