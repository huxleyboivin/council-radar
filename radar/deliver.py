"""Deliver an issue through Buttondown (which also handles Stripe billing and unsubscribes).

Buttondown is the source of truth for who gets the issue once BUTTONDOWN_API_KEY exists
(see ops/buttondown_migration.md). Audiences are tags:
  active       paying subscribers
  trial-1      trial readers due their first issue
  trial-2      trial readers due their second (last) issue
  trial-ended  finished trials (never emailed by this module)
Each audience gets its own email, filtered by tag, so trial readers see "trial issue N of 2"
and everyone gets the CASL footer. No subscriber data is ever written to this (public) repo.
"""
from __future__ import annotations

import re
from pathlib import Path

import requests

from . import config

API_ROOT = "https://api.buttondown.com/v1"
API = f"{API_ROOT}/emails"
# Pin the API version so behaviour doesn't change under us (docs.buttondown.com/api-versioning).
API_VERSION = "2026-11-10"

TAG_ACTIVE = "active"
TAG_TRIALS = ("trial-1", "trial-2")
TAG_TRIAL_ENDED = "trial-ended"

# Same links and wording as ops/weekly_task.md (prices, Stripe links and the CASL footer are Huxley's;
# change them there and here together, only on his say-so).
STRIPE_FOUNDING = "https://buy.stripe.com/eVqaEZ3ZGbwjc1Qdm38Vi00"
STRIPE_TEAM = "https://buy.stripe.com/4gM8wRfIo9ob4zobdV8Vi01"
BILLING_PORTAL = "https://billing.stripe.com/p/login/eVqaEZ3ZGbwjc1Qdm38Vi00"
FOOTER = (f"Manage or cancel your subscription: {BILLING_PORTAL} · Council Radar, 230 Regina Street North, "
          "Waterloo, ON · Reply 'unsubscribe' to stop these emails.")


def trial_line(n: int) -> str:
    return (f"This is trial issue {n} of 2. To keep getting it: {STRIPE_FOUNDING} ($59/month founding rate) "
            f"or {STRIPE_TEAM} (team of 5, $249/month).")


def _headers(sending: bool = False) -> dict:
    h = {"Authorization": f"Token {config.BUTTONDOWN_API_KEY}", "X-API-Version": API_VERSION}
    if sending:
        # Required (API 2026-04-01+) the first time a key creates an email with status about_to_send.
        h["X-Buttondown-Live-Dangerously"] = "true"
    return h


def _need_key():
    if not config.BUTTONDOWN_API_KEY:
        raise RuntimeError("BUTTONDOWN_API_KEY is not set")


def tag_filter(tag_id: str) -> dict:
    """Buttondown FilterGroup selecting subscribers who have the tag (filters take the tag ID, not its name)."""
    return {"filters": [{"field": "subscriber.tags", "operator": "contains", "value": tag_id}],
            "groups": [], "predicate": "and"}


def send(subject: str, body_markdown: str, mode: str | None = None, session=None, filters: dict | None = None) -> dict:
    """mode="draft" creates a draft to review in Buttondown; mode="send" sends to subscribers."""
    _need_key()
    mode = mode or config.DELIVERY_MODE
    payload = {"subject": subject, "body": body_markdown,
               "status": "about_to_send" if mode == "send" else "draft"}
    if filters:
        payload["filters"] = filters
    s = session or requests
    r = s.post(API, json=payload, timeout=60, headers=_headers(sending=mode == "send"))
    if r.status_code >= 400:
        raise RuntimeError(f"Buttondown error {r.status_code}: {r.text[:500]}")
    return r.json()


def tag_ids(session=None) -> dict[str, str]:
    """Map tag name -> tag ID for the newsletter's tags."""
    _need_key()
    s = session or requests
    out, url = {}, f"{API_ROOT}/tags"
    while url:
        r = s.get(url, timeout=60, headers=_headers())
        if r.status_code >= 400:
            raise RuntimeError(f"Buttondown error {r.status_code}: {r.text[:500]}")
        data = r.json()
        out.update({t["name"]: t["id"] for t in data.get("results", [])})
        url = data.get("next")
    return out


def issue_from_markdown(path: Path) -> tuple[str, str]:
    """Subject and body of an issue rendered by `radar render` (data/issues/<date>-<feed>.md)."""
    body = Path(path).read_text()
    title = re.search(r"^# (.+)$", body, re.M)
    week = re.search(r"^\*Week of (.+?)\*$", body, re.M)
    if not (title and week):
        raise ValueError(f"{path} doesn't look like a rendered issue (no '# title' / '*Week of ...*' lines)")
    return f"{title.group(1).strip()} | week of {week.group(1).strip()}", body


def plan_weekly(subject: str, body: str) -> list[dict]:
    """One email per audience: paying subscribers, then each trial step."""
    plan = [{"tag": TAG_ACTIVE, "subject": subject, "body": f"{body.rstrip()}\n\n{FOOTER}\n"}]
    for n, tag in enumerate(TAG_TRIALS, start=1):
        plan.append({"tag": tag, "subject": subject,
                     "body": f"{body.rstrip()}\n\n{trial_line(n)}\n\n{FOOTER}\n"})
    return plan


def send_weekly(subject: str, body: str, mode: str | None = None, session=None) -> list[dict]:
    """Send (or draft) the issue to every audience whose tag exists. Returns one result per audience."""
    ids = tag_ids(session)
    results = []
    for item in plan_weekly(subject, body):
        tid = ids.get(item["tag"])
        if not tid:
            results.append({"tag": item["tag"], "skipped": "tag does not exist yet"})
            continue
        res = send(item["subject"], item["body"], mode=mode, session=session, filters=tag_filter(tid))
        results.append({"tag": item["tag"], "id": res.get("id"), "status": res.get("status")})
    return results


def advance_trials(session=None) -> list[str]:
    """After a real send: trial-2 -> trial-ended, then trial-1 -> trial-2. Returns the changes made.

    Order matters (trial-2 first) so nobody moves two steps in one run. VERIFY ON THE FIRST LIVE RUN:
    the docs don't say whether PATCH tags replaces or merges, so we check the response and stop if the
    old tag is still there (otherwise that reader would get two emails next week).
    """
    _need_key()
    s = session or requests
    changes = []
    for old, new in ((TAG_TRIALS[1], TAG_TRIAL_ENDED), (TAG_TRIALS[0], TAG_TRIALS[1])):
        url, params = f"{API_ROOT}/subscribers", {"tag": old}
        subs = []
        while url:
            r = s.get(url, params=params, timeout=60, headers=_headers())
            if r.status_code >= 400:
                raise RuntimeError(f"Buttondown error {r.status_code}: {r.text[:500]}")
            data = r.json()
            subs += data.get("results", [])
            url, params = data.get("next"), None
        for sub in subs:
            tags = [t for t in sub.get("tags", []) if t != old] + [new]
            r = s.patch(f"{API_ROOT}/subscribers/{sub['id']}", json={"tags": tags}, timeout=60, headers=_headers())
            if r.status_code >= 400:
                raise RuntimeError(f"Buttondown error {r.status_code}: {r.text[:500]}")
            if old in r.json().get("tags", []):
                raise RuntimeError(f"PATCH merged tags instead of replacing them (subscriber {sub['id']}); "
                                   "fix advance_trials before the next send")
            changes.append(f"{sub['id']}: {old} -> {new}")
    return changes
