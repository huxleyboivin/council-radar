"""Build the public Ontario municipal support tracker (site/tracker.html).

Public, free page that earns search traffic and trust: council decisions on IESO energy projects
(support granted, refused, new protocols) plus the list of councils we monitor. Early signals,
delegations and staff reports stay subscriber-only, and live findings show up here only
PUBLIC_DELAY_DAYS after their meeting, so subscribers still hear first.
"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

from . import config

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
PUBLIC_DELAY_DAYS = 14
PUBLIC_CATEGORIES = [
    ("support_granted", "Support granted"),
    ("support_denied", "Support refused or not yet given"),
    ("policy_protocol", "New protocols and criteria"),
]
TRIAL_MAILTO = ("mailto:councilradaron@gmail.com?subject=Free%20trial%20issue&body=Hi%20Huxley%2C%20"
                "I%27d%20like%20a%20free%20trial%20issue%20of%20Council%20Radar.%20Councils%20I%20care%20about%3A%20")


def _date_key(d: str) -> str:
    return (d or "")[:10]


def _parse_date(d: str) -> date | None:
    m = re.match(r"(\d{4})-(\d{2})(?:-(\d{2}))?", d or "")
    if not m:
        return None
    return date(int(m[1]), int(m[2]), int(m[3] or 1))


def _pretty_date(d: str) -> str:
    p = _parse_date(d)
    if not p:
        return d or ""
    return p.strftime("%B %-d, %Y") if len(d) >= 10 else p.strftime("%B %Y")


def collect_items(today: date | None = None) -> list[dict]:
    today = today or date.today()
    items: list[dict] = []
    seed = config.DATA_DIR / "tracker_seed.json"
    if seed.exists():
        items += json.loads(seed.read_text())
    sys.path.insert(0, str(ROOT))
    try:
        from samples.build_sample import ITEMS  # verified public items used in the sample issue
        items += ITEMS
    except Exception:
        pass
    cutoff = today - timedelta(days=PUBLIC_DELAY_DAYS)
    for f in sorted((config.DATA_DIR / "issues").glob("*-findings.json")):
        try:
            live = json.loads(f.read_text())
        except Exception:
            continue
        for it in live:
            d = _parse_date(it.get("meeting_date", ""))
            if d and d <= cutoff:
                items.append(it)
    seen, out = set(), []
    for it in items:
        if it.get("category") not in dict(PUBLIC_CATEGORIES):
            continue
        key = (it.get("municipality"), (it.get("headline") or "").lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    out.sort(key=lambda i: _date_key(i.get("meeting_date", "")), reverse=True)
    return out


def coverage() -> list[str]:
    import yaml
    munis = yaml.safe_load((config.ROOT / "municipalities.yaml").read_text()) or []
    extra = config.DATA_DIR / "discovered.yaml"
    if extra.exists():
        munis += yaml.safe_load(extra.read_text()) or []
    return sorted({m["name"] for m in munis}, key=lambda n: re.sub(r"^(City|Town|Township|Municipality|County|Village|United Counties|Region|Regional Municipality) of ", "", n))


def _portals() -> dict[str, str]:
    """Monitored council name -> its public meeting portal."""
    import yaml
    munis = yaml.safe_load((config.ROOT / "municipalities.yaml").read_text()) or []
    extra = config.DATA_DIR / "discovered.yaml"
    if extra.exists():
        munis += yaml.safe_load(extra.read_text()) or []
    return {m["name"]: f"https://pub-{m['slug']}.escribemeetings.com" for m in munis
            if m.get("platform", "escribe") == "escribe" and m.get("slug")}


# ---------------------------------------------------------------------------
# "Check your council" lookup on the landing page.
# Every Ontario municipality, whether we read it, what's public about it, how many
# subscriber-only items it has had lately (count only), and its next meetings.
# ---------------------------------------------------------------------------
LOCKED_WINDOW_DAYS = 90
_KIND_RE = re.compile(r"^(City|Town|Township|Municipality|County|Village|Region|United Counties|Regional Municipality) of (.+)$")
_KIND_ALIAS = {"united counties": "county", "regional municipality": "region"}


def _muni_key(name: str) -> tuple[str, str]:
    """('haldimand', 'county') for both 'Haldimand County' and 'Haldimand (County)'."""
    name = (name or "").strip()
    m = re.match(r"^(.+?) \((\w+)\)$", name) or None
    if m:
        core, kind = m[1], m[2]
    elif (m := _KIND_RE.match(name)):
        kind, core = m[1], m[2]
    elif name.endswith(" County"):
        core, kind = name[:-7], "County"
    else:
        core, kind = name, ""
    kind = kind.lower()
    return core.strip().lower(), _KIND_ALIAS.get(kind, kind)


def _ontario_municipalities() -> list[str]:
    f = config.DATA_DIR / "ontario_municipalities.txt"
    if not f.exists():
        return []
    out = []
    for line in f.read_text().splitlines():
        m = re.match(r"^(.+?) \((\w+)\)$", line.strip())
        if m:
            out.append(f"{m[2]} of {m[1]}")
    return out


def _when(start: str) -> str:
    """'2026-11-24T19:00:00' -> 'Tue, Nov 24, 7 p.m.' (meeting times are local)."""
    try:
        from datetime import datetime
        d = datetime.fromisoformat(start[:19])
    except ValueError:
        return start[:10]
    day = d.strftime("%a, %b %-d")
    if d.hour == 0 and d.minute == 0:
        return day
    h = d.hour % 12 or 12
    t = f"{h}:{d.minute:02d}" if d.minute else f"{h}"
    return f"{day}, {t} {'a.m.' if d.hour < 12 else 'p.m.'}"


_MEETING_LIKELY = re.compile(r"council|planning|committee of the whole|general (government )?committee|"
                            r"adjustment|development|infrastructure|public meeting|special", re.I)
_MEETING_UNLIKELY = re.compile(r"advisory|accessib|library|\bbia\b|police|o\.?p\.?p|heritage|museum|diversity|"
                              r"youth|senior|arts|health|board of management|orientation|closed", re.I)


def _meeting_rank(name: str) -> int:
    """0 = where energy items usually come up, 2 = rarely."""
    name = name or ""
    if _MEETING_UNLIKELY.search(name):
        return 2
    return 0 if _MEETING_LIKELY.search(name) else 1


def council_index(public: list[dict], today: date | None = None) -> dict:
    today = today or date.today()
    portals = _portals()
    entries: dict[tuple[str, str], dict] = {}
    for name in _ontario_municipalities():
        entries.setdefault(_muni_key(name), {"n": name})
    for name in coverage():
        e = entries.setdefault(_muni_key(name), {"n": name})
        e["n"] = name  # the name we use everywhere else wins
        e["c"] = 1
        if name in portals:
            e["p"] = portals[name]

    covered = set(coverage())

    def entry(muni: str) -> dict:
        return entries.setdefault(_muni_key(muni), {"n": muni})

    public_keys = set()
    for it in public:
        public_keys.add((it.get("municipality"), (it.get("headline") or "").lower()))
        entry(it.get("municipality", "")).setdefault("i", []).append(
            [it.get("category"), _pretty_date(it.get("meeting_date", "")), it.get("headline", ""), it.get("source_url", "")])

    # Early signals already published in the public sample issue (delegations, pitches).
    try:
        from samples.build_sample import ITEMS as SAMPLE_ITEMS
    except Exception:
        SAMPLE_ITEMS = []
    for it in SAMPLE_ITEMS:
        key = (it.get("municipality"), (it.get("headline") or "").lower())
        if it.get("category") in dict(PUBLIC_CATEGORIES) or key in public_keys:
            continue
        public_keys.add(key)
        entry(it.get("municipality", "")).setdefault("i", []).append(
            ["delegation", _pretty_date(it.get("meeting_date", "")), it.get("headline", ""), it.get("source_url", "")])

    # Subscriber-only items: count them, never show them.
    since = today - timedelta(days=LOCKED_WINDOW_DAYS)
    locked: set[tuple[str, str]] = set()
    live = []
    for f in sorted((config.DATA_DIR / "issues").glob("*-findings.json")):
        try:
            live += json.loads(f.read_text())
        except Exception:
            continue
    import sqlite3
    db = None
    if config.DB_PATH.exists():
        db = sqlite3.connect(config.DB_PATH)
        try:
            live += [{"municipality": m, "headline": h, "meeting_date": d} for m, h, d in
                     db.execute("SELECT municipality, headline, meeting_date FROM findings")]
        except sqlite3.Error:
            pass
    for it in live:
        key = (it.get("municipality"), (it.get("headline") or "").lower())
        d = _parse_date(it.get("meeting_date", ""))
        if key in public_keys or key in locked or not d or d < since:
            continue
        locked.add(key)
        e = entry(it["municipality"])
        e["l"] = e.get("l", 0) + 1

    meta = {"built": today.isoformat(), "public_delay": PUBLIC_DELAY_DAYS, "locked_days": LOCKED_WINDOW_DAYS}
    lt2 = lt2_timeline()
    if lt2:
        meta["lt2"] = lt2
    latest = sorted((config.DATA_DIR / "issues").glob("*-findings.json"))
    if latest:
        try:
            week = json.loads(latest[-1].read_text())
            meta["week"] = {"date": latest[-1].name[:10], "items": len(week),
                            "councils": len({w.get("municipality") for w in week})}
        except Exception:
            pass
    if db is not None:
        try:
            q = ("SELECT m.municipality, COUNT(DISTINCT m.meeting_id), COUNT(d.doc_key) "
                 "FROM meetings m LEFT JOIN documents d ON d.meeting_id = m.meeting_id GROUP BY m.municipality")
            for muni, meetings, docs in db.execute(q):
                e = entry(muni)
                e["m"], e["d"] = meetings, docs
            seen_meetings, upcoming = set(), {}
            flagged = flagged_meetings()
            for mid, muni, name, start, url in db.execute(
                    "SELECT meeting_id, municipality, name, start, url FROM meetings WHERE start >= ? ORDER BY start, name",
                    (today.isoformat(),)):
                k = (muni, start, re.sub(r"\W|of|meeting", "", (name or "").lower()))
                if k in seen_meetings:
                    continue
                seen_meetings.add(k)
                upcoming.setdefault(muni, []).append((_meeting_rank(name), start, name, url))
            # "This week" for the calendar showcase: flagged meetings first, then main council meetings.
            monday = today - timedelta(days=today.weekday())
            week = []
            for mid, muni, name, start, url in db.execute(
                    "SELECT meeting_id, municipality, name, start, url FROM meetings WHERE start >= ? AND start < ? "
                    "ORDER BY start", (monday.isoformat(), (monday + timedelta(days=7)).isoformat())):
                if muni in covered and _meeting_rank(name) == 0:
                    week.append(((mid or "").lower() in flagged, start, muni, name, url))
            pick = [w for w in week if w[0]][:3]
            used, days = {w[2] for w in pick}, {}
            for w in week:  # then one main council meeting per day, different councils
                if not w[0] and re.search(r"council", w[3], re.I) and w[2] not in used and w[1][:10] not in days:
                    days[w[1][:10]] = w
                    used.add(w[2])
            pick += list(days.values())[: 7 - len(pick)]
            meta["week_cal"] = [[_short_council(m), n, st[:10], _when(st), int(f), u]
                                for f, st, m, n, u in sorted(pick, key=lambda w: w[1])]
            for muni, rows in upcoming.items():
                best, kinds = [], set()  # where energy items land first, one per kind, then soonest
                for r in sorted(rows):
                    kind = re.sub(r"[\s\-–]*(panel|no\.?)?\s*\d+$", "", r[2] or "", flags=re.I).lower()
                    if kind not in kinds and len(best) < 3:
                        kinds.add(kind)
                        best.append(r)
                entry(muni)["u"] = [[n, _when(st), u] for _, st, n, u in sorted(best, key=lambda r: r[1])]
            # Workload of checking by hand: relevant meetings and their documents, last 30 days.
            lo = (today - timedelta(days=30)).isoformat()
            hi = (today + timedelta(days=1)).isoformat()
            k_tot = r_tot = 0
            for muni, name, docs in db.execute(
                    "SELECT m.municipality, m.name, COUNT(d.doc_key) FROM meetings m "
                    "LEFT JOIN documents d ON d.meeting_id = m.meeting_id "
                    "WHERE m.start >= ? AND m.start < ? GROUP BY m.meeting_id", (lo, hi)):
                if muni not in covered or _meeting_rank(name) >= 2:
                    continue
                e = entry(muni)
                e["k"] = e.get("k", 0) + 1
                e["r"] = e.get("r", 0) + docs
                k_tot, r_tot = k_tot + 1, r_tot + docs
            meta["month"] = {"meetings": k_tot, "documents": r_tot,
                             "councils": sum(1 for e in entries.values() if e.get("k"))}
            meta["documents"] = db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            meta["meetings"] = db.execute("SELECT COUNT(*) FROM meetings").fetchone()[0]
            row = db.execute("SELECT finished_at FROM runs WHERE kind='run' AND finished_at IS NOT NULL "
                             "ORDER BY id DESC LIMIT 1").fetchone()
            if row and row[0]:
                meta["last_run"] = row[0]
        except sqlite3.Error:
            pass
        db.close()
    councils = sorted(entries.values(), key=lambda e: _muni_key(e["n"]))
    meta["covered"] = sum(1 for e in councils if e.get("c"))
    meta["total"] = len(councils)
    return {"meta": meta, "councils": councils}


def _e(s) -> str:
    return html.escape(str(s or ""))


def render(items: list[dict], councils: list[str], built: date) -> str:
    sections = []
    for cat, label in PUBLIC_CATEGORIES:
        rows = [i for i in items if i.get("category") == cat]
        if not rows:
            continue
        lis = []
        for i in rows:
            bits = [i.get("municipality"), _pretty_date(i.get("meeting_date", ""))]
            tech = i.get("technology")
            if i.get("capacity_mw"):
                tech = f"{i['capacity_mw']} MW {tech.lower() if tech else ''}".strip()
            if tech:
                bits.append(tech)
            if i.get("proponent"):
                bits.append(i["proponent"])
            src = f' <a href="{_e(i["source_url"])}" rel="nofollow">Source</a>' if i.get("source_url") else ""
            where = [_e(b) for b in bits if b]
            if i.get("municipality"):  # link each decision to that council's page (internal links help search engines)
                where[0] = f'<a href="councils/{council_slug(i["municipality"])}/">{_e(i["municipality"])}</a>'
            lis.append(
                f'<li data-muni="{_e(i.get("municipality", "")).lower()}"><h3>{_e(i.get("headline"))}</h3>'
                f'<p class="where">{" / ".join(where)}</p>'
                f'<p>{_e(i.get("summary"))}{src}</p></li>')
        sections.append(f'<section><h2>{label} <span class="n">{len(rows)}</span></h2><ul class="feed">{"".join(lis)}</ul></section>')
    council_list = "".join(f'<li><a href="councils/{council_slug(c)}/">{_e(c)}</a></li>' for c in councils)
    return PAGE.format(
        sections="".join(sections) or "<p>No public decisions yet.</p>",
        n_items=len(items), n_councils=len(councils), councils=council_list,
        built=built.strftime("%B %-d, %Y"), delay=PUBLIC_DELAY_DAYS, trial=TRIAL_MAILTO)


PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ontario municipal support tracker for IESO projects | Council Radar</title>
<meta name="description" content="Which Ontario councils granted or refused municipal support for LT2 and LLT energy projects, and which have adopted protocols. Free, sourced, updated weekly. {n_councils} councils monitored.">
<link rel="canonical" href="https://huxleyboivin.github.io/council-radar/tracker.html">
<meta property="og:title" content="Ontario municipal support tracker for IESO energy projects"><meta property="og:description" content="Which Ontario councils gave or refused support for energy projects, and which adopted new rules. Free and sourced."><meta property="og:url" content="https://huxleyboivin.github.io/council-radar/tracker.html"><meta property="og:type" content="website"><meta property="og:site_name" content="Council Radar">
<meta property="og:image" content="https://huxleyboivin.github.io/council-radar/og/tracker.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{{--paper:#FFFFFF;--ink:#14284B;--text:#1F2D44;--muted:#52607A;--rule:#D5DCE5;--mist:#EEF3F8;--line:#2F6FB5}}
body{{margin:0;background:var(--paper);color:var(--text);font:400 1.0625rem/1.65 "Public Sans",system-ui,sans-serif}}
main{{max-width:46rem;margin:0 auto;padding:2rem 1.5rem 4rem}}
a{{color:var(--line)}} a:focus-visible,input:focus-visible{{outline:3px solid var(--line);outline-offset:3px}}
h1{{font:700 2.2rem/1.15 "Public Sans",sans-serif;letter-spacing:-.02em;color:var(--ink);margin:1.5rem 0 .6rem}}
h2{{font:700 1.3rem/1.3 "Public Sans",sans-serif;color:var(--ink);margin:2.6rem 0 .6rem;padding-top:1.1rem;border-top:1px solid var(--rule)}}
h2 .n{{font:500 .95rem "Public Sans",sans-serif;color:var(--muted)}}
h3{{font:600 1.08rem/1.4 "Public Sans",sans-serif;color:var(--ink);margin:0 0 .15rem}}
.lede{{color:var(--muted);max-width:38rem}}
.feed{{list-style:none;padding:0;margin:0}} .feed li{{padding:1rem 0;border-bottom:1px solid var(--rule)}}
.feed p{{margin:.2rem 0}} .where{{color:var(--muted);font-size:.92rem}}
.cta{{background:var(--mist);border-radius:10px;padding:1.25rem 1.5rem;margin:1.8rem 0}}
.cta p{{margin:.2rem 0}} .btns a{{display:inline-block;margin:.5rem 1rem .2rem 0;font-weight:600}} .btns a:first-child{{background:var(--ink);color:#fff;text-decoration:none;padding:.7rem 1.05rem;border-radius:6px}}
label{{display:block;font-weight:500;margin-top:1.2rem}}
input{{font:inherit;padding:.6rem .8rem;border:1px solid var(--rule);border-radius:6px;width:min(100%,22rem);background:#fff;color:var(--ink)}}
.councils{{columns:2 15rem;padding-left:1.1rem;font-size:.95rem}}
.small{{font-size:.9rem;color:var(--muted)}}
</style></head>
<body><main>
<a href="index.html">Back to Council Radar</a>
<h1>Ontario municipal support tracker</h1>
<p class="lede">IESO projects on municipal land need support from the local council. This free page lists the council decisions and protocols we've confirmed, each with a link to the source. It's updated weekly, and decisions are added {delay} days after subscribers receive them.</p>
<div class="cta"><p><strong>Want them the week they happen?</strong> Subscribers also see requests and presentations before councils decide.</p>
<p class="btns"><a href="index.html#pricing">Subscribe for $59 a month</a><a href="{trial}">Get a free trial issue</a></p></div>
<label for="q">Filter by municipality</label><input id="q" type="search" placeholder="e.g. Haldimand" autocomplete="off">
{sections}
<section><h2>Councils we monitor <span class="n">{n_councils}</span></h2>
<p class="small">We read agendas, staff reports and minutes from these councils every day. Need one that isn't listed? <a href="{trial}">Tell us</a> and we'll prioritize it.</p>
<ul class="councils">{councils}</ul></section>
<p class="small">Last updated {built}. Council Radar · 230 Regina Street North, Waterloo, ON.</p>
</main>
<script>
const q=document.getElementById("q");
function f(){{const v=q.value.trim().toLowerCase();
document.querySelectorAll(".feed li").forEach(li=>{{li.hidden=v&&!li.dataset.muni.includes(v);}});}}
q.addEventListener("input",f);
const pre=new URLSearchParams(location.search).get("q");if(pre){{q.value=pre;f();}}
</script><script src="start.js"></script>
</body></html>"""


# ---------------------------------------------------------------------------
# Free calendar feeds: one .ics per council we read, rebuilt on every deploy.
# Meetings with an energy item we found are marked; what the item is stays in
# the subscriber email.
# ---------------------------------------------------------------------------
SITE_URL = config.SITE_URL
CAL_PAST_DAYS = 30
_TZ_BLOCK = (
    "BEGIN:VTIMEZONE\r\nTZID:America/Toronto\r\n"
    "BEGIN:DAYLIGHT\r\nTZOFFSETFROM:-0500\r\nTZOFFSETTO:-0400\r\nTZNAME:EDT\r\nDTSTART:19700308T020000\r\n"
    "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU\r\nEND:DAYLIGHT\r\n"
    "BEGIN:STANDARD\r\nTZOFFSETFROM:-0400\r\nTZOFFSETTO:-0500\r\nTZNAME:EST\r\nDTSTART:19701101T020000\r\n"
    "RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU\r\nEND:STANDARD\r\nEND:VTIMEZONE\r\n")


def council_slug(name: str) -> str:
    """Same slug the site's JavaScript builds: 'Township of Wellesley' -> 'township-of-wellesley'."""
    import unicodedata
    s = "".join(ch for ch in unicodedata.normalize("NFD", name or "") if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip().replace(" ", "-")


def _ics_text(s: str) -> str:
    return (s or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r", "").replace("\n", "\\n")


def _ics_fold(line: str) -> str:
    out, cur = [], b""
    for ch in line:
        b = ch.encode("utf-8")
        if len(cur) + len(b) > (75 if not out else 74):
            out.append(cur.decode("utf-8"))
            cur = b""
        cur += b
    out.append(cur.decode("utf-8"))
    return "\r\n ".join(out) + "\r\n"


def _short_council(name: str) -> str:
    core, kind = _muni_key(name)
    m = _KIND_RE.match(name)
    short = m[2] if m else (name[:-7] if name.endswith(" County") else name)
    return short + (" County" if kind == "county" else "")


def flagged_meetings() -> set[str]:
    """Meeting IDs where we found an energy item (from live findings and the database)."""
    urls = []
    for f in sorted((config.DATA_DIR / "issues").glob("*-findings.json")):
        try:
            urls += [it.get("source_url", "") for it in json.loads(f.read_text())]
        except Exception:
            continue
    if config.DB_PATH.exists():
        import sqlite3
        db = sqlite3.connect(config.DB_PATH)
        try:
            urls += [u for (u,) in db.execute("SELECT source_url FROM findings")]
        except sqlite3.Error:
            pass
        db.close()
    return {m[1].lower() for u in urls if u and (m := re.search(r"[?&]Id=([0-9a-fA-F-]{36})", u))}


def lt2_timeline() -> dict | None:
    """Window 2 milestones from data/lt2_timeline.json (edited by hand as the IESO confirms dates)."""
    f = config.DATA_DIR / "lt2_timeline.json"
    if not f.exists():
        return None
    try:
        data = json.loads(f.read_text())
    except ValueError:
        return None
    return {k: v for k, v in data.items() if not k.startswith("_")}


def write_lt2_calendar(out_dir: Path) -> bool:
    """site/cal/lt2-window-2.ics: the Window 2 milestones as all-day events."""
    from datetime import datetime, timezone
    lt2 = lt2_timeline()
    if not lt2:
        return False
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Council Radar//LT2 Window 2//EN", "CALSCALE:GREGORIAN",
             "METHOD:PUBLISH", f"X-WR-CALNAME:{_ics_text(lt2.get('name', 'LT2 Window 2') + ' milestones')}",
             f"X-WR-CALDESC:{_ics_text('IESO LT2 Window 2 milestones, kept current by Council Radar. Dates marked expected are approximate.')}",
             "REFRESH-INTERVAL;VALUE=DURATION:PT12H", "X-PUBLISHED-TTL:PT12H"]
    body = "".join(_ics_fold(l) for l in lines)
    for m in lt2.get("milestones", []):
        d = date.fromisoformat(m["plot"])
        desc = f"{m.get('when', '')}. {m.get('detail', '')}\n\nSource: {m.get('source', '')}\n\nCouncil Radar: {SITE_URL}"
        ev = ["BEGIN:VEVENT", f"UID:lt2w2-{m['key']}@council-radar", f"DTSTAMP:{stamp}",
              f"DTSTART;VALUE=DATE:{d:%Y%m%d}", f"DTEND;VALUE=DATE:{d + timedelta(days=1):%Y%m%d}",
              f"SUMMARY:{_ics_text(('Window 2: ' + m['label']) + (' (expected)' if m.get('approx') else ''))}",
              f"DESCRIPTION:{_ics_text(desc.replace(chr(92) + 'n', chr(10)))}", "TRANSP:TRANSPARENT", "END:VEVENT"]
        body += "".join(_ics_fold(l) for l in ev)
    body += "END:VCALENDAR\r\n"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "lt2-window-2.ics").write_bytes(body.encode("utf-8"))
    return True


def write_calendars(today: date | None = None, out_dir: Path | None = None) -> int:
    from datetime import datetime, timezone
    import sqlite3
    today = today or date.today()
    out_dir = out_dir or SITE / "cal"
    out_dir.mkdir(parents=True, exist_ok=True)
    flagged = flagged_meetings()
    meetings: dict[str, list] = {}
    if config.DB_PATH.exists():
        db = sqlite3.connect(config.DB_PATH)
        since = (today - timedelta(days=CAL_PAST_DAYS)).isoformat()
        for mid, muni, name, start, url in db.execute(
                "SELECT meeting_id, municipality, name, start, url FROM meetings WHERE start >= ? ORDER BY start", (since,)):
            if _meeting_rank(name) < 2 and start:
                meetings.setdefault(muni, []).append((mid, name, start, url))
        db.close()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    n = 0
    for council in coverage():
        slug = council_slug(council)
        short = _short_council(council)
        brief = f"{SITE_URL}brief.html?c={slug}"
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Council Radar//Council meetings//EN",
                 "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
                 f"X-WR-CALNAME:{_ics_text(short + ' council meetings')}",
                 f"X-WR-CALDESC:{_ics_text(f'Upcoming {council} meetings with agenda links, updated every morning by Council Radar. Meetings marked ⚡ have an energy item on the agenda.')}",
                 "X-WR-TIMEZONE:America/Toronto", "REFRESH-INTERVAL;VALUE=DURATION:PT12H", "X-PUBLISHED-TTL:PT12H"]
        body = "".join(_ics_fold(l) for l in lines) + _TZ_BLOCK
        seen = set()
        for mid, name, start, url in meetings.get(council, []):
            key = (start, re.sub(r"\W|of|meeting", "", (name or "").lower()))
            if key in seen:
                continue
            seen.add(key)
            try:
                d = datetime.fromisoformat(start[:19])
            except ValueError:
                continue
            flag = (mid or "").lower() in flagged
            summary = f"{'⚡ ' if flag else ''}{short}: {name}"
            if flag:
                note = (f"Council Radar found an energy item on this agenda. Subscribers get what it is, "
                        f"who is behind it and what council decided in Monday's email.\n\n"
                        f"Get it free in a trial issue: {brief}")
            else:
                note = (f"Council Radar reads this agenda when it's posted and flags solar, wind, battery storage "
                        f"and gas projects. If one comes up, this event gets a ⚡.\n\n"
                        f"See what we'd send you for {council}: {brief}")
            desc = f"Agenda and documents: {url}\n\n{note}\n\nTimes as posted by the municipality. Not legal advice."
            ev = ["BEGIN:VEVENT", f"UID:{mid}@council-radar", f"DTSTAMP:{stamp}"]
            if d.hour == 0 and d.minute == 0:
                ev += [f"DTSTART;VALUE=DATE:{d:%Y%m%d}", f"DTEND;VALUE=DATE:{d + timedelta(days=1):%Y%m%d}"]
            else:
                ev += [f"DTSTART;TZID=America/Toronto:{d:%Y%m%dT%H%M%S}",
                       f"DTEND;TZID=America/Toronto:{d + timedelta(hours=2):%Y%m%dT%H%M%S}"]
            ev += [f"SUMMARY:{_ics_text(summary)}", f"DESCRIPTION:{_ics_text(desc)}"]
            if url:
                ev.append(f"URL:{url}")
            ev += ["TRANSP:TRANSPARENT", "END:VEVENT"]
            body += "".join(_ics_fold(l) for l in ev)
        body += "END:VCALENDAR\r\n"
        (out_dir / f"{slug}.ics").write_bytes(body.encode("utf-8"))
        n += 1
    write_lt2_calendar(out_dir)
    return n


def _rebase_static_pages() -> None:
    """Hand-written pages (index, sample, brief, tracker) carry the GitHub Pages URL in canonical and share tags.
    When the site moves to its own domain (site/CNAME), point them at the new address."""
    if SITE_URL == config.GITHUB_PAGES_URL:
        return
    for page in ("index.html", "sample.html", "brief.html", "tracker.html"):
        f = SITE / page
        if f.exists():
            f.write_text(f.read_text().replace(config.GITHUB_PAGES_URL, SITE_URL))


def build(today: date | None = None) -> Path:
    today = today or date.today()
    items = collect_items(today)
    councils = coverage()
    out = SITE / "tracker.html"
    out.write_text(render(items, councils, today))
    idx = SITE / "index.html"
    index = council_index(items, today)
    from . import council_pages
    pages = council_pages.write(index, today, council_slug, _when, _meeting_rank)
    try:  # share-card images; the site still works without them
        from . import og_images
        cards = og_images.write_all(index, council_pages._upcoming(config.DB_PATH, today, _meeting_rank), council_slug, _when)
    except Exception as exc:  # noqa: BLE001
        print(f"share cards skipped: {exc}")
        cards = 0
    if idx.exists():
        s = idx.read_text()
        s = re.sub(r"<!--COVERAGE-->.*?<!--/COVERAGE-->", f"<!--COVERAGE-->{len(councils)}<!--/COVERAGE-->", s)
        raw = json.dumps(index, separators=(",", ":"), ensure_ascii=False)
        (config.ROOT / "site" / "councils.json").write_text(raw)  # read by brief.html
        data = raw.replace("</", "<\\/")
        s = re.sub(r"<!--COUNCILDATA-->.*?<!--/COUNCILDATA-->",
                   lambda _: f'<!--COUNCILDATA--><script type="application/json" id="council-data">{data}</script><!--/COUNCILDATA-->',
                   s, flags=re.S)
        idx.write_text(s)
    from . import guides
    with_pages = {c["n"]: council_slug(c["n"]) for c in index["councils"] if c.get("c") or c.get("i")}
    guide_pages = guides.write(today, with_pages)
    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"<url><loc>{SITE_URL}{p}</loc><lastmod>{today}</lastmod></url>\n"
                  for p in ("", "tracker.html", "sample.html", *guide_pages, *pages))
        + "</urlset>\n")
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n")
    _rebase_static_pages()
    cals = write_calendars(today)
    print(json.dumps({"tracker": str(out), "items": len(items), "councils": len(councils), "calendars": cals, "council_pages": len(pages) - 1, "share_cards": cards}))
    return out
