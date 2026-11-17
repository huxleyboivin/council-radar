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
            lis.append(
                f'<li data-muni="{_e(i.get("municipality", "")).lower()}"><h3>{_e(i.get("headline"))}</h3>'
                f'<p class="where">{" / ".join(_e(b) for b in bits if b)}</p>'
                f'<p>{_e(i.get("summary"))}{src}</p></li>')
        sections.append(f'<section><h2>{label} <span class="n">{len(rows)}</span></h2><ul class="feed">{"".join(lis)}</ul></section>')
    council_list = "".join(f"<li>{_e(c)}</li>" for c in councils)
    return PAGE.format(
        sections="".join(sections) or "<p>No public decisions yet.</p>",
        n_items=len(items), n_councils=len(councils), councils=council_list,
        built=built.strftime("%B %-d, %Y"), delay=PUBLIC_DELAY_DAYS, trial=TRIAL_MAILTO)


PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ontario municipal support tracker for IESO energy projects | Council Radar</title>
<meta name="description" content="Which Ontario councils granted or refused municipal support for LT2 and LLT energy projects, and which have adopted protocols. Free, sourced, updated weekly. {n_councils} councils monitored.">
<link rel="canonical" href="https://huxleyboivin.github.io/council-radar/tracker.html">
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
q.addEventListener("input",()=>{{const v=q.value.trim().toLowerCase();
document.querySelectorAll(".feed li").forEach(li=>{{li.hidden=v&&!li.dataset.muni.includes(v);}});}});
</script></body></html>"""


def build(today: date | None = None) -> Path:
    today = today or date.today()
    items = collect_items(today)
    councils = coverage()
    out = SITE / "tracker.html"
    out.write_text(render(items, councils, today))
    idx = SITE / "index.html"
    if idx.exists():
        s = idx.read_text()
        s = re.sub(r"<!--COVERAGE-->.*?<!--/COVERAGE-->", f"<!--COVERAGE-->{len(councils)}<!--/COVERAGE-->", s)
        idx.write_text(s)
    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"<url><loc>https://huxleyboivin.github.io/council-radar/{p}</loc><lastmod>{today}</lastmod></url>\n"
                  for p in ("", "tracker.html", "sample.html"))
        + "</urlset>\n")
    print(json.dumps({"tracker": str(out), "items": len(items), "councils": len(councils)}))
    return out
