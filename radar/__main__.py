"""Command line entry point.

  python -m radar run        # collect new documents, prefilter, AI-read, store findings
  python -m radar digest     # build this week's issue per enabled feed and deliver it
  python -m radar discover   # probe Ontario municipalities for eScribe portals
  python -m radar health     # write data/health.json (read by the maintenance agent)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
from datetime import date, datetime, timedelta
from pathlib import Path

import yaml

from . import tracker, analyze, config, deliver, digest, escribe, prefilter, store


def load_municipalities() -> list[dict]:
    munis = yaml.safe_load((config.ROOT / "municipalities.yaml").read_text()) or []
    extra = config.DATA_DIR / "discovered.yaml"
    if extra.exists():
        known = {m["slug"] for m in munis}
        munis += [m for m in (yaml.safe_load(extra.read_text()) or []) if m["slug"] not in known]
    return munis


def excerpt_dir() -> Path:
    return config.DATA_DIR / "excerpts"


def save_excerpt(feed: str, doc_key: str, meta: dict, hits: int, text: str) -> Path:
    day = date.today().isoformat()
    d = excerpt_dir() / day
    d.mkdir(parents=True, exist_ok=True)
    path = d / (feed + "__" + re.sub(r"[^A-Za-z0-9_.-]+", "_", doc_key) + ".json")
    path.write_text(json.dumps({"feed": feed, "doc_key": doc_key, "saved": day, "hits": hits,
                                **meta, "excerpt": text}, indent=1))
    return path


def cmd_pending(args) -> int:
    """Print excerpts saved after the last issue (input for the weekly Claude task)."""
    last_file = config.DATA_DIR / "issues" / "last_issue.txt"
    since = args.since or (last_file.read_text().strip() if last_file.exists() else "0000-00-00")
    out = []
    if excerpt_dir().exists():
        for day in sorted(p for p in excerpt_dir().iterdir() if p.is_dir() and p.name > since):
            for f in sorted(day.glob(f"{args.feed}__*.json")):
                out.append(json.loads(f.read_text()))
    print(json.dumps({"since": since, "count": len(out), "excerpts": out}, indent=1))
    return 0


def cmd_render(args) -> int:
    """Render an issue from a findings JSON file written by the weekly Claude task."""
    feeds = prefilter.load_feeds()
    items = json.loads(Path(args.findings).read_text())
    subject, body = digest.render(items, feeds[args.feed].title)
    out_dir = config.DATA_DIR / "issues"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{date.today().isoformat()}-{args.feed}.md"
    path.write_text(body)
    # keep the findings so the public tracker can publish decisions after the delay
    (out_dir / f"{date.today().isoformat()}-{args.feed}-findings.json").write_text(json.dumps(items, indent=1))
    if args.mark_done:
        (out_dir / "last_issue.txt").write_text(date.today().isoformat())
    print(json.dumps({"subject": subject, "path": str(path)}))
    return 0


def cmd_run(args) -> int:
    started = store.now()
    con = store.connect()
    # enabled feeds are read and sent; collect-only (beta) feeds are read so we build a sample, never sent
    feeds = {k: f for k, f in prefilter.load_feeds().items() if f.enabled or f.collect}
    fetcher = escribe.Fetcher()
    client = analyze._client() if config.ANTHROPIC_API_KEY else None
    today = date.today()
    start, end = today - timedelta(days=config.LOOKBACK_DAYS), today + timedelta(days=config.LOOKAHEAD_DAYS)
    stats = {"municipalities": 0, "meetings": 0, "documents": 0, "skipped": 0, "matched": 0,
             "ai_reads": 0, "findings": 0, "errors": []}
    munis = load_municipalities()
    if args.only:
        munis = [m for m in munis if m["slug"] in args.only.split(",")]
    for muni in munis:
        if muni.get("platform") != "escribe":
            continue
        slug, name = muni["slug"], muni["name"]
        try:
            meetings = escribe.list_meetings(fetcher, slug, start, end)
        except Exception as e:
            stats["errors"].append({"municipality": slug, "stage": "list", "error": repr(e)[:300]})
            continue
        stats["municipalities"] += 1
        for m in meetings:
            stats["meetings"] += 1
            store.upsert_meeting(con, m, name, slug)
            if not m.has_agenda:
                continue  # nothing published yet; check again tomorrow
            upcoming = m.start is None or m.start.date() >= today - timedelta(days=2)
            try:
                docs = list(escribe.iter_meeting_documents(fetcher, slug, m))
            except escribe.Blocked as e:
                stats["errors"].append({"municipality": slug, "stage": "blocked", "meeting": m.url,
                                        "error": "bot verification page; not retried"})
                continue
            except Exception as e:
                stats["errors"].append({"municipality": slug, "stage": "meeting", "meeting": m.url,
                                        "error": repr(e)[:300]})
                continue
            for doc_key, title, url, text in docs:
                prior = store.doc_status(con, doc_key)
                if prior and prior["status"] == "ok" and not upcoming and not getattr(args, "refresh", False):
                    stats["skipped"] += 1
                    continue  # attachments don't change; past agendas are final
                try:
                    if text is None:
                        text = escribe.fetch_document_text(fetcher, escribe.DocLink(doc_key.split(":")[-1], url, title))
                except Exception as e:
                    store.save_document(con, doc_key, m.meeting_id, title, url, None, "error", repr(e)[:300])
                    continue
                h = store.sha(text or "")
                store.save_document(con, doc_key, m.meeting_id, title, url, h)
                stats["documents"] += 1
                for fkey, feed in feeds.items():
                    # a read is keyed on text + the feed's patterns, so editing feeds.yaml re-scans
                    rh = store.sha(h + "|" + "|".join(p.pattern for p in feed.patterns))
                    if store.already_read(con, doc_key, fkey, rh):
                        continue
                    hits, excerpt = prefilter.excerpt(text or "", feed)
                    meta = {"doc_title": title, "municipality": name, "meeting_name": m.name,
                            "meeting_date": m.start.date().isoformat() if m.start else "unknown", "url": url}
                    if hits and client is None:
                        # No-cost mode: save the matched passages; the weekly Claude scheduled task reads them.
                        stats["matched"] += 1
                        save_excerpt(fkey, doc_key, meta, hits, excerpt)
                        stats["excerpts_saved"] = stats.get("excerpts_saved", 0) + 1
                    elif hits:
                        stats["matched"] += 1
                        try:
                            items = analyze.read(feed, excerpt, meta, client=client)
                            stats["ai_reads"] += 1
                        except Exception as e:
                            stats["errors"].append({"municipality": slug, "stage": "ai", "doc": doc_key,
                                                    "error": repr(e)[:300]})
                            continue
                        for it in items:
                            it.update(doc_key=doc_key, municipality=name, meeting_name=m.name,
                                      meeting_date=meta["meeting_date"], source_url=url)
                            if store.save_finding(con, fkey, it):
                                stats["findings"] += 1
                    store.mark_read(con, doc_key, fkey, rh, hits)
            con.commit()
    store.log_run(con, "run", started, stats)
    con.commit()
    print(json.dumps({k: v for k, v in stats.items() if k != "errors"} | {"errors": len(stats["errors"])}))
    (config.DATA_DIR / "last_run_errors.json").write_text(json.dumps(stats["errors"], indent=1))
    return 0


def cmd_digest(args) -> int:
    con = store.connect()
    feeds = {k: f for k, f in prefilter.load_feeds().items() if f.enabled}
    out_dir = config.DATA_DIR / "issues"
    out_dir.mkdir(parents=True, exist_ok=True)
    for key, feed in feeds.items():
        rows = store.unsent_findings(con, key)
        subject, body = digest.render(rows, feed.title)
        path = out_dir / f"{date.today().isoformat()}-{key}.md"
        path.write_text(body)
        print(f"{key}: {len(rows)} findings -> {path}")
        if args.deliver:
            if not rows and not args.send_empty:
                print(f"{key}: nothing new; not delivering")
                continue
            res = deliver.send(subject, body)
            store.mark_sent(con, [r["id"] for r in rows], str(res.get("id", "sent")))
            con.commit()
    return 0


def parse_name_line(line: str) -> tuple[str, str]:
    """'Minto (Town)' -> ('Minto', 'town')"""
    m = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", line)
    return (m.group(1).strip(), m.group(2).strip().lower()) if m else (line.strip(), "")


def display_name(name: str, kind: str) -> str:
    return f"{kind.title()} of {name}" if kind else name


def slug_candidates(line: str) -> list[str]:
    name, kind = parse_name_line(line)
    n = name.lower().replace("&", "and").replace("'", "").replace("é", "e").replace("ô", "o")
    words = re.findall(r"[a-z0-9]+", n)
    core = [w for w in words if w != "the"] if words and words[0] == "the" else words
    joined, k = "".join(core), kind.replace(" ", "")
    out = [joined, "".join(words)]
    if k:
        out += [joined + k, k + joined, k + "of" + joined]
    out += ["-".join(core)]
    seen, res = set(), []
    for s in out:
        if s and s not in seen:
            seen.add(s)
            res.append(s)
    return res


def cmd_discover(args) -> int:
    names_file = config.DATA_DIR / "ontario_municipalities.txt"
    names = [l.strip() for l in names_file.read_text().splitlines() if l.strip() and not l.startswith("#")]
    known = {m["slug"] for m in load_municipalities()}
    fetcher = escribe.Fetcher(delay=0.5)
    found = []
    for name in names:
        for slug in slug_candidates(name):
            if slug in known:
                break
            try:
                fetcher._wait()  # keep probes spaced out
                r = fetcher.s.get(escribe.base_url(slug) + "/", timeout=15, allow_redirects=False)
            except Exception:
                continue
            if r.status_code == 200 and "escribe" in r.text.lower():
                found.append({"name": display_name(*parse_name_line(name)), "platform": "escribe", "slug": slug})
                known.add(slug)
                print("found", name, slug)
                break
    out = config.DATA_DIR / "discovered.yaml"
    prev = yaml.safe_load(out.read_text()) if out.exists() else []
    out.write_text(yaml.safe_dump((prev or []) + found, sort_keys=False))
    print(f"discovered {len(found)} new portals")
    return 0


OTHER_PLATFORMS = {
    # platform: (url template, marker that must appear in the page)
    "civicweb": ("https://{slug}.civicweb.net/Portal/", "civicweb"),
    "icompass": ("https://{slug}.icompasscanada.com/", "icompass"),
}


def cmd_survey(args) -> int:
    """Find which other agenda platforms the councils we don't cover yet use (no parsing, just a count)."""
    names_file = config.DATA_DIR / "ontario_municipalities.txt"
    names = [l.strip() for l in names_file.read_text().splitlines() if l.strip() and not l.startswith("#")]
    covered = {m["name"] for m in load_municipalities()}
    fetcher = escribe.Fetcher(delay=0.4)
    found = []
    for line in names:
        disp = display_name(*parse_name_line(line))
        if disp in covered:
            continue
        hit = None
        for platform, (tmpl, marker) in OTHER_PLATFORMS.items():
            for slug in slug_candidates(line)[:3]:
                try:
                    fetcher._wait()
                    r = fetcher.s.get(tmpl.format(slug=slug), timeout=15, allow_redirects=True)
                except Exception:
                    continue
                if r.status_code == 200 and marker in r.text.lower():
                    hit = {"name": disp, "platform": platform, "slug": slug}
                    break
            if hit:
                break
        if hit:
            found.append(hit)
            print("found", hit["platform"], disp, hit["slug"])
    out = config.DATA_DIR / "platform_survey.yaml"
    out.write_text(yaml.safe_dump(found, sort_keys=False))
    from collections import Counter
    print("survey:", dict(Counter(f["platform"] for f in found)), "of", len(names) - len(covered), "uncovered")
    return 0


def cmd_debug(args) -> int:
    """Print a raw calendar item and the links found on one agenda page (for parser repairs)."""
    f = escribe.Fetcher()
    today = date.today()
    base = escribe.base_url(args.slug)
    r = f.post_json(base + "/MeetingsCalendarView.aspx/GetCalendarMeetings",
                    {"calendarStartDate": (today - timedelta(days=21)).isoformat(),
                     "calendarEndDate": (today + timedelta(days=21)).isoformat()})
    items = r.json().get("d", [])
    print("calendar items:", len(items))
    print(json.dumps(items[:2], indent=1, default=str)[:3000])
    print("robots.txt:", f.s.get(base + "/robots.txt", timeout=20).text[:500])
    meetings = [m for m in escribe.parse_calendar_json(r.json(), args.slug) if m.docs]
    if meetings:
        d = meetings[0].docs[0]
        print("doc:", d.url, d.title)
        tests = {
            "plain": {},
            "referer": {"Referer": escribe.agenda_url(meetings[0])},
            "referer+accept": {"Referer": escribe.agenda_url(meetings[0]),
                               "Accept": "application/pdf,text/html;q=0.9,*/*;q=0.8"},
        }
        f.get(escribe.agenda_url(meetings[0]))  # pick up any session cookie first
        for name, h in tests.items():
            resp = f.s.get(d.url, headers=h, timeout=60)
            print(f"download[{name}]:", resp.status_code, resp.headers.get("Content-Type"),
                  resp.headers.get("Server"), len(resp.content), resp.text[:150].replace("\n", " ") if resp.status_code != 200 else "")
        m = meetings[0]
        page = f.get(escribe.agenda_url(m))
        print("agenda url:", escribe.agenda_url(m), page.status_code, len(page.text))
        text, docs = escribe.parse_meeting_page(page.text, args.slug)
        print("agenda text chars:", len(text), "docs:", [(d.doc_id, d.title[:60]) for d in docs[:10]])
    return 0


def cmd_health(args) -> int:
    con = store.connect()
    runs = [dict(r) for r in con.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 14")]
    for r in runs:
        r["stats"] = json.loads(r["stats"] or "{}")
    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    report = {
        "generated": store.now(),
        "municipalities_configured": len(load_municipalities()),
        "recent_runs": runs,
        "findings_last_7_days": con.execute("SELECT COUNT(*) FROM findings WHERE created_at>=?", (week_ago,)).fetchone()[0],
        "unsent_findings": {r["feed"]: r["n"] for r in con.execute(
            "SELECT feed, COUNT(*) n FROM findings WHERE issue_id IS NULL GROUP BY feed")},
        "document_errors_last_7_days": con.execute(
            "SELECT COUNT(*) FROM documents WHERE status='error' AND fetched_at>=?", (week_ago,)).fetchone()[0],
    }
    (config.DATA_DIR / "health.json").write_text(json.dumps(report, indent=1, default=str))
    print(json.dumps(report, indent=1, default=str)[:3000])
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="radar")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("--only", help="comma-separated slugs")
    r.add_argument("--refresh", action="store_true", help="re-fetch past agendas in the window (after editing feeds.yaml)")
    d = sub.add_parser("digest"); d.add_argument("--deliver", action="store_true")
    d.add_argument("--send-empty", action="store_true")
    sub.add_parser("discover"); sub.add_parser("health")
    pe = sub.add_parser("pending"); pe.add_argument("--feed", default="energy"); pe.add_argument("--since")
    rn = sub.add_parser("render"); rn.add_argument("--feed", default="energy")
    rn.add_argument("--findings", required=True); rn.add_argument("--mark-done", action="store_true")
    dbg = sub.add_parser("debug"); dbg.add_argument("slug")
    sub.add_parser("tracker"); sub.add_parser("survey")
    args = p.parse_args(argv)
    try:
        return {"run": cmd_run, "digest": cmd_digest, "discover": cmd_discover, "health": cmd_health,
                "pending": cmd_pending, "render": cmd_render, "debug": cmd_debug,
                "tracker": lambda a: (tracker.build(), 0)[1], "survey": cmd_survey}[args.cmd](args)
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
