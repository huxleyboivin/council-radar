"""One public page per council: /councils/<slug>/ plus a directory at /councils/.

Built on every deploy from the same data as the homepage lookup (tracker.council_index), so
search engines can find what the lookup shows: a council's public energy decisions and early
signals, its next meetings, a calendar feed and a way to start a trial for that council.
Subscriber-only items are counted, never shown. The output is gitignored (site/councils/).
"""
from __future__ import annotations

import html
import json
import shutil
import sqlite3
from datetime import date, timedelta
from urllib.parse import quote
from pathlib import Path

from . import config

SITE_URL = config.SITE_URL
LABEL = {"support_granted": ("Support given", "t-granted"), "support_denied": ("Refused or not yet given", "t-refused"),
         "policy_protocol": ("New rules", "t-rules"), "delegation": ("Early signal", "t-signal")}


def _e(s) -> str:
    return html.escape(str(s or ""))


CSS = """@view-transition{navigation:auto}

:root{--ink:#14284B;--text:#1F2D44;--muted:#52607A;--line:#D5DCE5;--mist:#EEF3F8;--blue:#2F6FB5;--granted:#2E7D4F;--refused:#B23A3A}
*{box-sizing:border-box}[hidden]{display:none!important}
body{margin:0;background:#fff;color:var(--text);font:400 1.0625rem/1.65 "Public Sans",system-ui,-apple-system,"Segoe UI",sans-serif;-webkit-font-smoothing:antialiased}
a{color:var(--blue)}a:focus-visible,button:focus-visible,input:focus-visible{outline:3px solid var(--blue);outline-offset:2px}
.top{max-width:62rem;margin:0 auto;padding:1rem 1.5rem;display:flex;align-items:center;justify-content:space-between;gap:1rem}
.brand{white-space:nowrap;display:flex;align-items:center;gap:.55rem;font-weight:700;color:var(--ink);text-decoration:none;font-size:1.05rem}
.nav{display:flex;gap:1.2rem;align-items:center;font-size:.95rem}.nav a{color:var(--text);text-decoration:none}.nav a:hover{color:var(--blue)}
.btn{display:inline-block;text-align:center;font:600 1rem/1.2 "Public Sans",system-ui,sans-serif;text-decoration:none;border-radius:8px;padding:.85rem 1.2rem;border:2px solid var(--ink);cursor:pointer}
.btn.primary{background:var(--ink);color:#fff}.btn.primary:hover{background:#0d1c36}
.btn.secondary{background:#fff;color:var(--ink)}.btn.secondary:hover{background:var(--mist)}
.btn.small{padding:.5rem .8rem;font-size:.92rem}
main{max-width:62rem;margin:0 auto;padding:0 1.5rem 4rem}
.crumbs{font-size:.88rem;color:var(--muted);margin:.6rem 0 0}.crumbs a{color:var(--muted)}
h1{font:700 clamp(2rem,4.2vw,2.9rem)/1.1 "Public Sans",sans-serif;letter-spacing:-.025em;color:var(--ink);margin:.7rem 0 .7rem;max-width:20ch}
.lede{font-size:1.15rem;color:var(--muted);max-width:42rem;margin:0 0 1.2rem}
.nextmtg{font-size:1.02rem;margin:-.4rem 0 1rem;padding:.6rem .85rem;background:var(--mist);border-radius:8px;display:inline-block}
.status{display:flex;flex-wrap:wrap;gap:.5rem 1rem;align-items:center;font-size:.92rem;color:var(--muted);margin:0 0 1.8rem}
.badge{font:600 .72rem/1 "Public Sans",sans-serif;letter-spacing:.03em;text-transform:uppercase;padding:.32rem .45rem;border-radius:4px}
.badge.on{background:#DDF1E4;color:#1D5C38}.badge.off{background:#E7EBF1;color:#3F4B60}
.grid{display:grid;grid-template-columns:minmax(0,1fr) 19rem;gap:2.5rem;align-items:start}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:.7rem;margin:0 0 1.6rem}
.stat{border:1px solid var(--line);border-radius:10px;padding:.85rem .9rem}
.stat strong{display:block;font:700 1.8rem/1.1 "Public Sans",sans-serif;color:var(--ink)}.stat span{font-size:.88rem;color:var(--muted)}
h2{font:700 1.25rem/1.3 "Public Sans",sans-serif;color:var(--ink);margin:2rem 0 .5rem;padding-top:1rem;border-top:1px solid var(--line)}
h2:first-of-type{margin-top:0}
ul.rows{list-style:none;margin:0;padding:0}
ul.rows li{padding:.75rem 0;border-bottom:1px solid #EDF1F6}ul.rows li:last-child{border-bottom:0}
.rows .h{display:block;font-weight:600;color:var(--ink);line-height:1.4}
.rows .m{font-size:.9rem;color:var(--muted)}
.tag{display:inline-flex;align-items:center;gap:.35rem;font:600 .82rem/1 "Public Sans",sans-serif;margin-bottom:.3rem}
.tag::before{content:"";width:.5rem;height:.5rem;border-radius:50%;background:currentColor}
.t-granted{color:var(--granted)}.t-refused{color:var(--refused)}.t-rules{color:var(--blue)}.t-signal{color:#B7791F}
.none{color:var(--muted);margin:.3rem 0}
.locked{display:flex;gap:.7rem;align-items:flex-start;margin:1rem 0 0;padding:.9rem 1rem;border:1px dashed #9AA8BD;border-radius:8px;font-size:.96rem;background:repeating-linear-gradient(-45deg,#fff,#fff 8px,#F6F8FB 8px,#F6F8FB 16px)}
.redact{display:block;height:.75rem;border-radius:3px;background:#DDE3EB;margin:.35rem 0}
.side{position:sticky;top:1rem;display:grid;gap:1rem}
.box{border:1px solid var(--line);border-radius:12px;padding:1.1rem 1.15rem}
.box.dark{background:var(--ink);border-color:var(--ink);color:#C9D4E6}
.box h3{font:700 1.05rem/1.3 "Public Sans",sans-serif;margin:0 0 .4rem;color:var(--ink)}.box.dark h3{color:#fff}
.box p{margin:0 0 .8rem;font-size:.94rem}
.box .btn{display:block;width:100%;margin-top:.5rem}
.box.dark .btn.primary{background:#fff;color:var(--ink);border-color:#fff}
.box.dark .btn.secondary{background:transparent;color:#fff;border-color:#8FA3C3}
.box.w2{border-left:4px solid #B23A3A}.box.w2 p{margin:0 0 .55rem}
.w2k{font:700 .74rem/1 "Public Sans",sans-serif!important;letter-spacing:.07em;text-transform:uppercase;color:#B23A3A}
.w2n{font:700 1.7rem/1.1 "Public Sans",sans-serif!important;color:var(--ink);letter-spacing:-.02em;margin:.2rem 0 .2rem!important}
.w2s{font-size:.84rem!important;color:var(--muted)}
.cal a,.share .links a,.linkish{display:inline-block;margin:0 .7rem .3rem 0;font-weight:600;font-size:.94rem}
.linkish{background:none;border:0;padding:0;color:var(--blue);text-decoration:underline;cursor:pointer;font-family:inherit}
.share .btn{margin:0 0 .7rem;width:auto;display:inline-block}.share .links{margin:0}.copied{font-size:.86rem;color:var(--granted);margin:.3rem 0 0;min-height:1.2em}
.about{font-size:.94rem;color:var(--muted);margin-top:2.4rem;padding-top:1rem;border-top:1px solid var(--line)}
footer{border-top:1px solid var(--line);padding:1.6rem 1.5rem;text-align:center;font-size:.9rem;color:var(--muted)}
/* directory */
.dir-search{width:100%;max-width:28rem;font:500 1.05rem/1.2 "Public Sans",sans-serif;padding:.8rem .9rem;border:2px solid var(--ink);border-radius:9px;margin:0 0 1.4rem}
.dir{columns:3 16rem;column-gap:2rem;list-style:none;margin:0;padding:0}
.dir li{break-inside:avoid;padding:.3rem 0;font-size:.98rem}
.dir li small{color:var(--muted);font-size:.8rem;margin-left:.3rem}
.dir .letter{font:700 .8rem/1 "Public Sans",sans-serif;letter-spacing:.08em;color:var(--muted);padding-top:.9rem}
@media (max-width:860px){.grid{grid-template-columns:minmax(0,1fr);gap:1.5rem}.side{position:static;order:-1}.nav .hide-sm{display:none}.stats{gap:.4rem}.stat{padding:.65rem}.stat strong{font-size:1.45rem}}
"""

LOGO = ('<svg width="26" height="26" viewBox="0 0 26 26" aria-hidden="true"><circle cx="13" cy="13" r="11.5" fill="none" '
        'stroke="#14284B" stroke-width="2"/><circle cx="13" cy="13" r="6" fill="none" stroke="#2F6FB5" stroke-width="2"/>'
        '<path d="M13 13 L22.5 6.5" stroke="#14284B" stroke-width="2" stroke-linecap="round"/></svg>')


def _shell(title: str, desc: str, canonical: str, root: str, body: str, ld: dict | None = None, image: str = "") -> str:
    ld_tag = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>' if ld else ""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(title)}</title>
<meta name="description" content="{_e(desc)}">
<link rel="canonical" href="{_e(canonical)}">
<meta property="og:title" content="{_e(title)}"><meta property="og:description" content="{_e(desc)}"><meta property="og:url" content="{_e(canonical)}"><meta property="og:type" content="website"><meta property="og:site_name" content="Council Radar">
<meta property="og:image" content="{_e(image or SITE_URL + "og/councils.png")}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 26 26'%3E%3Ccircle cx='13' cy='13' r='11.5' fill='none' stroke='%2314284B' stroke-width='2'/%3E%3Ccircle cx='13' cy='13' r='6' fill='none' stroke='%232F6FB5' stroke-width='2'/%3E%3Cpath d='M13 13 L22.5 6.5' stroke='%2314284B' stroke-width='2' stroke-linecap='round'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style>{ld_tag}{config.analytics_snippet()}
</head><body>
<header class="top"><a class="brand" href="{root}index.html">{LOGO}Council Radar</a>
<nav class="nav" aria-label="Main"><a href="{root}councils/">Councils</a><a href="{root}guides/">Guides</a><a class="hide-sm" href="{root}sample.html">Sample issue</a><a class="hide-sm" href="{root}housing.html">Housing</a><a class="hide-sm" href="{root}tracker.html">Tracker</a>
<a class="btn primary small" href="{root}index.html#pricing">Subscribe</a></nav></header>
{body}
<footer>Council Radar reads public municipal records and summarizes them. It isn't legal advice. We count visits with Google Analytics. <a href="{root}index.html">Home</a> · <a href="{root}councils/">All councils</a> · <a href="{root}guides/">Guides</a> · <a href="mailto:councilradaron@gmail.com">councilradaron@gmail.com</a></footer>
<script src="{root}start.js"></script>
<script>
(function(){{
  document.querySelectorAll("[data-share]").forEach(function(b){{
    if(!navigator.share){{b.hidden=true;return;}}
    b.addEventListener("click",function(){{navigator.share({{title:b.dataset.title,url:b.dataset.url}}).catch(function(){{}});}});
  }});
  document.querySelectorAll("[data-copy-url]").forEach(function(b){{
    b.addEventListener("click",function(){{var n=b.closest(".box").querySelector(".copied");
      (navigator.clipboard?navigator.clipboard.writeText(b.dataset.copyUrl):Promise.reject()).then(function(){{n.textContent="Link copied.";}},function(){{n.textContent=b.dataset.copyUrl;}});}});
  }});
}})();
</script>
</body></html>
"""


def _upcoming(db_path: Path, today: date, rank) -> dict[str, list]:
    out: dict[str, list] = {}
    if not db_path.exists():
        return out
    db = sqlite3.connect(db_path)
    try:
        seen = set()
        for muni, name, start, url in db.execute(
                "SELECT municipality, name, start, url FROM meetings WHERE start >= ? AND start < ? ORDER BY start",
                (today.isoformat(), (today + timedelta(days=60)).isoformat())):
            k = (muni, start, (name or "").lower())
            if k in seen or rank(name) >= 2:
                continue
            seen.add(k)
            if len(out.setdefault(muni, [])) < 8:
                out[muni].append((name, start, url))
    finally:
        db.close()
    return out


def _span(today: date, to: date) -> str | None:
    days = (to - today).days
    if days <= 0:
        return None
    if days < 21:
        return f"{days} day{'s' if days != 1 else ''}"
    if days < 60:
        return f"about {round(days / 7)} weeks"
    return f"about {round(days / 30.44)} months"


def clock_box(meta: dict, name: str, upcoming: list, when, today: date) -> str:
    """Window 2 countdown for one council (static; rebuilt every deploy)."""
    lt2 = meta.get("lt2") or {}
    ms = lt2.get("milestones") or []
    due = next((m for m in ms if m.get("deadline")), None)
    if not due:
        return ""
    left = _span(today, date.fromisoformat(due["plot"]))
    pre = next((m for m in ms if m.get("key") == "pre"), None)
    nxt = next((u for u in upcoming if "council" in (u[0] or "").lower()), upcoming[0] if upcoming else None)
    ics = f"{SITE_URL}cal/lt2-window-2.ics"
    webcal = "webcal://" + ics.split("://", 1)[1]
    head = f"{left[0].upper() + left[1:]}" if left else "Due now"
    out = (f'<div class="box w2"><p class="w2k">{_e(lt2.get("name", "LT2 Window 2"))} clock</p>'
           f'<p class="w2n">{_e(head)}</p><p>until proposals are due ({_e(due.get("when", ""))}). Every proposal for a project in '
           f'{_e(name)} needs this council\'s support when it\'s submitted.</p>')
    if pre:
        pl = _span(today, date.fromisoformat(pre["plot"]))
        if pl:
            out += f'<p>Pre-engagement with the municipality: {_e(pl)} ({_e(pre.get("when", ""))}).</p>'
    if nxt:
        out += f'<p><strong>Next council meeting:</strong> {_e(nxt[0])}, {_e(when(nxt[1]).rstrip("."))}.</p>'
    out += (f'<p class="w2s">IESO timeline, approximate. <a href="{_e(webcal)}">Window 2 dates in your calendar</a> · '
            f'<a href="{_e(due.get("source", ""))}" rel="nofollow">Source</a></p></div>')
    return out


TITLE_MAX = 70  # Semrush flags titles over 70 characters; Google shows about 60


def _short_name(name: str) -> str:
    """'Municipality of Southwest Middlesex' -> 'Southwest Middlesex'; 'Haldimand County' stays."""
    return name.split(" of ", 1)[1] if " of " in name else name


def search_name(name: str) -> str:
    """The council's name as people type it into Google (Semrush, Canada, November 2026).

    Cities and counties are searched with the type after the name ("ottawa city council" 480/mo vs "ottawa council"
    170; "oxford county council" 110 vs "oxford council" 20), regions as "<name> region council" ("peel region
    council" 210), except Waterloo ("region of waterloo council" 170 vs 90). Towns, townships and municipalities are
    searched by the bare name ("whitby council" 170 vs "whitby town council" 50)."""
    short = _short_name(name)
    if name.startswith("City of"):
        return f"{short} City Council"
    if name.startswith("County of"):
        return f"{short} County Council"
    if name == "Region of Waterloo":
        return "Region of Waterloo Council"
    if name.startswith("Region of"):
        return f"{short} Region Council"
    if name.endswith(" County"):
        return f"{name} Council"
    return f"{short} Council"


def page_title(name: str) -> str:
    """Matches how people search ("<town> council meeting") and stays short enough not to be cut off."""
    for t in (f"{search_name(name)}: meetings & energy decisions | Council Radar",
              f"{search_name(name)}: meetings & energy decisions",
              f"{_short_name(name)} council: meetings & energy decisions"):
        if len(t) <= TITLE_MAX:
            return t
    return f"{_short_name(name)} council meetings"


def _next_council(upcoming: list):
    """The next meeting of council itself, else the next meeting of any kind."""
    return next((u for u in upcoming if "council" in (u[0] or "").lower()), upcoming[0] if upcoming else None)


# Councils with a guide about a project in or next to them. Searches like "wesleyville nuclear" and "darlington smr"
# outnumber searches for the council itself, so the council page points to the guide and the guide links back.
LOCAL_GUIDES = {
    "Municipality of Port Hope": ("new-nuclear-ontario", "OPG is studying up to 10,000 MWe of new nuclear at its Wesleyville site here"),
    "Municipality of Clarington": ("new-nuclear-ontario", "OPG is building the first Darlington small modular reactor here"),
    "Municipality of Kincardine": ("new-nuclear-ontario", "Bruce Power's proposed Bruce C project, up to 4,800 MWe, is here"),
    "Town of Saugeen Shores": ("new-nuclear-ontario", "Bruce Power's proposed Bruce C project is in neighbouring Kincardine"),
    "Town of Cobourg": ("new-nuclear-ontario", "OPG's proposed Wesleyville nuclear project is in neighbouring Port Hope"),
    "Municipality of West Grey": ("agrivoltaics-ontario", "The Cedar Agrivoltaics project here won an LT2 contract"),
    "Town of Minto": ("wind-projects-ontario", "A 70 MW wind proposal has been presented to this council"),
    "Township of Wellesley": ("wind-projects-ontario", "A 200 MW wind proposal has been presented to this council"),
}


def _local_guide(name: str, g: str) -> str:
    if name not in LOCAL_GUIDES:
        return ""
    slug, line = LOCAL_GUIDES[name]
    label = {"new-nuclear-ontario": "New nuclear projects in Ontario", "agrivoltaics-ontario": "Agrivoltaics in Ontario",
             "wind-projects-ontario": "Wind farms in Ontario"}[slug]
    return f'<p><strong>Local project:</strong> {_e(line)}. See <a href="{g}{slug}/">{label}</a>.</p>'


def how_support_works(name: str, root: str, covered: bool, n_meetings: int) -> str:
    """Plain-language background for every council page, with links to the guides."""
    g = f"{root}guides/"
    read = (f"Council Radar reads every {_e(name)} council, committee and planning agenda as it's posted"
            f"{f', {n_meetings:,} meetings so far' if n_meetings else ''}, so a support request shows up here and in the "
            f"Monday email before council votes.") if covered else (
            f"Council Radar doesn't read {_e(name)}'s agendas yet. Decisions shown here come from public reports and news.")
    return (f'<h2>How energy projects get support in {_e(name)}</h2>'
            f'<p>Under the IESO\'s Long-Term 2 (LT2) procurement, a solar, wind, battery storage or gas project in {_e(name)} '
            f'needs a <a href="{g}municipal-support-resolution/">municipal support resolution</a> from this council before the '
            f'developer can submit a proposal. Without it, the IESO won\'t consider the project. Council can vote on each project, '
            f'pass a blanket resolution for projects that meet its criteria, or delegate the decision to staff.</p>'
            f'<p>Proposals for <a href="{g}lt2-window-2/">LT2 Window 2</a> are expected to be due in mid-2027, and developers '
            f'must contact the municipality before that. The council elected on October 26, 2026 will make these decisions. '
            f'{read}</p>'
            f'{_local_guide(name, g)}'
            f'<p>Related: <a href="{g}lt2-window-1-results/">LT2 Window 1 results by municipality</a> · '
            f'<a href="{g}solar-and-battery-projects-ontario/">Solar and battery storage projects in Ontario</a> · '
            f'<a href="{g}where-ontario-councils-stand/">Where Ontario councils stand</a> · '
            f'<a href="{root}tracker.html">Municipal support tracker</a></p>')


def council_page(c: dict, meta: dict, upcoming: list, slug: str, when, today: date) -> str:
    name = c["n"]
    root = "../../"
    canonical = f"{SITE_URL}councils/{slug}/"
    items = c.get("i") or []
    locked = c.get("l", 0)
    covered = bool(c.get("c"))
    n_up = len(upcoming)

    title = page_title(name)
    if covered:
        desc = (f"{search_name(name)} meetings and agendas, plus its decisions on solar, wind, battery storage and gas "
                f"projects. Free calendar feed. Read every morning by Council Radar.")
    else:
        desc = f"What {name} council has decided on energy projects, from public records. Council Radar doesn't read this council's agendas yet."

    status = [f'<span class="badge {"on" if covered else "off"}">{"Read every morning" if covered else "Not read yet"}</span>']
    if covered and c.get("m"):
        status.append(f"{c['m']:,} meetings tracked")
    if covered and c.get("d"):
        status.append(f"{c['d']:,} documents read")
    status.append(f"Updated {today.strftime('%B %-d, %Y')}")

    stats = (f'<div class="stats"><div class="stat"><strong>{len(items)}</strong><span>public {"item" if len(items) == 1 else "items"}</span></div>'
             f'<div class="stat"><strong>{locked}</strong><span>subscriber {"item" if locked == 1 else "items"}, last {meta.get("locked_days", 90)} days</span></div>'
             f'<div class="stat"><strong>{c.get("k", 0) if covered else "–"}</strong><span>meetings, last 30 days</span></div></div>')

    if items:
        rows = []
        for cat, d, head, src in items:
            lab, cls = LABEL.get(cat, ("Item", "t-rules"))
            link = f' · <a href="{_e(src)}" rel="nofollow">Source</a>' if src else ""
            rows.append(f'<li><span class="tag {cls}">{lab}</span><span class="h">{_e(head)}</span><span class="m">{_e(d)}{link}</span></li>')
        decisions = f'<ul class="rows">{"".join(rows)}</ul>'
    elif covered:
        decisions = (f'<p class="none">No public energy decisions on record for {_e(name)} yet. A new council took office on '
                     f'November 15, 2026, so the first support requests of this term are still ahead.</p>')
    else:
        decisions = f'<p class="none">No public energy decisions on record for {_e(name)}.</p>'
    if locked:
        decisions += (f'<div class="locked"><span aria-hidden="true">🔒</span><div><strong>{locked} more '
                      f'{"item" if locked == 1 else "items"}</strong> about {_e(name)} from the last {meta.get("locked_days", 90)} days '
                      f'{"is" if locked == 1 else "are"} in the subscriber issue. Decisions become public here '
                      f'{meta.get("public_delay", 14)} days after subscribers get them.'
                      f'<span class="redact" style="width:85%"></span><span class="redact" style="width:60%"></span></div></div>')

    if covered:
        if upcoming:
            def _agenda(u):
                return f' · <a href="{_e(u)}" rel="nofollow">Agenda</a>' if u else ""
            meet = "".join(f'<li><span class="h">{_e(n)}</span><span class="m">{_e(when(st))}{_agenda(u)}</span></li>'
                           for n, st, u in upcoming)
            meetings = f'<ul class="rows">{meet}</ul>'
        else:
            portal = f' Its <a href="{_e(c["p"])}" rel="nofollow">meeting portal</a> is checked every morning.' if c.get("p") else ""
            meetings = f'<p class="none">No council, committee or planning meetings posted for the next 60 days yet.{portal}</p>'
    else:
        meetings = (f'<p class="none">We don\'t read {_e(name)}\'s agendas yet. Ask for it when you start a trial, '
                    f'and we\'ll prioritize adding it.</p>')

    ics = f"{SITE_URL}cal/{slug}.ics"
    webcal = "webcal://" + ics.split("://", 1)[1]
    cal_box = ""
    if covered:
        cal_box = (f'<div class="box cal"><h3>Meetings in your calendar, free</h3><p>Every {_e(name)} council, committee and '
                   f'planning meeting, with the agenda link. Meetings with an energy item get a ⚡.</p>'
                   f'<a href="https://outlook.office.com/calendar/0/addfromweb?url={quote(ics, safe="")}&amp;name={quote(name + " meetings")}" rel="noopener">Outlook</a>'
                   f'<a href="https://calendar.google.com/calendar/r?cid={quote(webcal, safe="")}" rel="noopener">Google</a>'
                   f'<a href="{_e(webcal)}">Apple</a><a href="{_e(ics)}">Feed link</a></div>')

    start_box = (f'<div class="box dark"><h3>Get {_e(name)} in your Monday email</h3>'
                 f'<p>Every agenda, staff report and set of minutes, read for solar, wind, battery storage and gas items. '
                 f'Your first issue is free.</p>'
                 f'<a class="btn primary" href="mailto:councilradaron@gmail.com?subject=Free%20trial%20issue" data-start data-councils="{_e(name)}">Start free</a>'
                 f'<a class="btn secondary" href="{root}brief.html?c={slug}" rel="nofollow">Preview your Monday email</a></div>')

    share_url = quote(canonical, safe="")
    share_text = quote(f"{name} council and energy projects: decisions, next meetings and a free calendar feed", safe="")
    share_box = (f'<div class="box share"><h3>Share this page</h3><p>Send it to your team, or post it where your project is being discussed.</p>'
                 f'<button type="button" class="btn secondary small" data-share data-url="{_e(canonical)}" data-title="{_e(name)} and energy projects">Share</button>'
                 f'<p class="links"><a href="https://www.linkedin.com/sharing/share-offsite/?url={share_url}" target="_blank" rel="noopener">LinkedIn</a>'
                 f'<a href="https://bsky.app/intent/compose?text={share_text}%20{share_url}" target="_blank" rel="noopener">Bluesky</a>'
                 f'<a href="https://www.reddit.com/submit?url={share_url}&amp;title={share_text}" target="_blank" rel="noopener">Reddit</a>'
                 f'<a href="mailto:?subject={share_text}&amp;body={share_url}">Email</a>'
                 f'<button type="button" class="linkish" data-copy-url="{_e(canonical)}">Copy link</button></p>'
                 f'<p class="copied" role="status"></p></div>')
    portal_line = (f' It reads the <a href="{_e(c["p"])}" rel="nofollow">{_e(name)} meeting portal</a> every morning.'
                   if c.get("p") else "")
    about = (f'<p class="about">Council Radar is a weekly email for energy developers, their lawyers and consultants. '
             f'It reads the agendas, staff reports and minutes of {meta.get("covered", 150)} Ontario councils and flags items about '
             f'energy projects.{portal_line} Public decisions appear on this page {meta.get("public_delay", 14)} days after '
             f'subscribers get them. <a href="{root}sample.html">See a sample issue</a>.</p>')

    nxt = _next_council(upcoming) if covered else None
    next_line = ""
    if nxt:
        agenda = f' · <a href="{_e(nxt[2])}" rel="nofollow">Agenda</a>' if nxt[2] else ""
        next_line = f'<p class="nextmtg"><strong>Next meeting:</strong> {_e(nxt[0])}, {_e(when(nxt[1]))}{agenda}</p>'
    body = f"""<main>
<p class="crumbs"><a href="{root}index.html">Home</a> › <a href="{root}councils/">Councils</a> › {_e(name)}</p>
<h1>{_e(name)} council meetings and energy projects</h1>
<p class="lede">Where {_e(name)} council stands on solar, wind, battery storage and gas projects, and when it meets next.</p>
{next_line}
<p class="status">{" · ".join(status)}</p>
<div class="grid"><div>
{stats}
<h2>Decisions, rules and early signals</h2>
{decisions}
<h2>Coming up</h2>
{meetings}
{how_support_works(name, root, covered, c.get("m", 0))}
{about}
</div><aside class="side">{clock_box(meta, name, upcoming, when, today) if covered else ""}{start_box}{cal_box}{share_box}</aside></div>
</main>"""
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Council Radar", "item": SITE_URL},
        {"@type": "ListItem", "position": 2, "name": "Councils", "item": SITE_URL + "councils/"},
        {"@type": "ListItem", "position": 3, "name": name, "item": canonical}]}
    return _shell(title, desc, canonical, root, body, ld, image=f"{SITE_URL}og/councils/{slug}.png")


def directory_page(entries: list[tuple[str, dict]], meta: dict) -> str:
    root = "../"
    rows, last = [], ""
    for slug, c in entries:
        letter = c["_sort"][0].upper()
        if letter != last:
            rows.append(f'<li class="letter" aria-hidden="true">{_e(letter)}</li>')
            last = letter
        note = []
        if c.get("i"):
            note.append(f'{len(c["i"])} public')
        if c.get("l"):
            note.append(f'{c["l"]} subscriber')
        if not c.get("c"):
            note.append("not read yet")
        small = "<small>" + _e(", ".join(note)) + "</small>" if note else ""
        rows.append(f'<li data-q="{_e(c["n"].lower())}"><a href="{slug}/">{_e(c["n"])}</a>{small}</li>')
    body = f"""<main>
<p class="crumbs"><a href="{root}index.html">Home</a> › Councils</p>
<h1>Ontario councils and energy projects</h1>
<p class="lede">{meta.get("covered", 150)} councils whose agendas, staff reports and minutes Council Radar reads every morning, plus councils with public energy decisions on record. Each page shows decisions, early signals and the next meetings.</p>
<label for="dir-q" class="crumbs" style="display:block;margin-bottom:.4rem">Find a council</label>
<input id="dir-q" class="dir-search" type="search" placeholder="Type a municipality" autocomplete="off">
<ul class="dir" id="dir">{"".join(rows)}</ul>
</main>
<script>
(function(){{var q=document.getElementById("dir-q");q.addEventListener("input",function(){{var v=q.value.trim().toLowerCase();
document.querySelectorAll("#dir li").forEach(function(li){{li.hidden=v?(!li.dataset.q||li.dataset.q.indexOf(v)<0):false;}});}});}})();
</script>"""
    title = "Ontario council meetings & energy decisions | Council Radar"
    desc = (f"Decisions, early signals and upcoming meetings on solar, wind, battery storage and gas projects for "
            f"{meta.get('covered', 150)} Ontario councils. Updated every morning.")
    return _shell(title, desc, SITE_URL + "councils/", root, body, image=SITE_URL + "og/councils.png")


def write(index: dict, today: date, slug, when, rank, out_dir: Path | None = None) -> list[str]:
    """Write all council pages and the directory. Returns site-relative paths for the sitemap."""
    out_dir = out_dir or (config.ROOT / "site" / "councils")
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    meta = index["meta"]
    upcoming = _upcoming(config.DB_PATH, today, rank)
    entries = []
    for c in index["councils"]:
        if not (c.get("c") or c.get("i")):
            continue  # nothing to say about it yet: no page
        s = slug(c["n"])
        c = dict(c, _sort=c["n"].split(" of ", 1)[-1] if " of " in c["n"] else c["n"])
        page = out_dir / s / "index.html"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(council_page(c, meta, upcoming.get(c["n"], []), s, when, today))
        entries.append((s, c))
    entries.sort(key=lambda e: e[1]["_sort"].lower())
    (out_dir / "index.html").write_text(directory_page(entries, meta))
    return ["councils/"] + [f"councils/{s}/" for s, _ in entries]
