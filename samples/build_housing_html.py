"""Render samples/housing-sample.md into site/housing.html: the Housing edition's landing + sample page.

Built from site/sample.html so it keeps the site's styles, analytics tag and start.js.
Stripe: dedicated 'Council Radar: Ontario Housing' product (prod_Vgjik3VMtFI1Oy) with its own $59 and $249 CAD/month
payment links, created 2026-11-24; still tagged ?client_reference_id=housing.

Since 2026-11-25 (web designer) the page opens with a housing front door:
- a "development proposal" notice sign that shows the sample's largest real projects (parsed from the markdown),
- a council lookup that shows how many council and committee meetings had housing items (counted from
  data/excerpts/*/housing__*.json; counts and meeting names only, never the item content) and the next meeting,
- the Start panel opened in the Housing edition (site/start.js), so trial requests and "skip the trial" checkouts
  go to the housing product.
`radar tracker` rebuilds this page on every deploy, so the counts stay current.
"""
import html
import json
import re
from datetime import date, timedelta
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
FOUNDING = "https://buy.stripe.com/eVqeVfcwceIv5Ds4Px8Vi02?client_reference_id=housing"
TEAM = "https://buy.stripe.com/4gM00l67O6bZ5DschZ8Vi03?client_reference_id=housing"
TRIAL = "mailto:councilradaron@gmail.com?subject=Free%20trial%20issue%20-%20Housing"
WINDOW_DAYS = 30
FONTS = ('<link href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@600;700'
         '&family=Public+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">')

e = html.escape
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def _day(iso: str) -> str:
    try:
        d = date.fromisoformat(iso[:10])
    except ValueError:
        return iso
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# ---------------- sample parsing ----------------

def sections(md: str) -> list[tuple[str, int]]:
    """(heading, number of items) for each ## section of the sample."""
    out = []
    for block in re.split(r"\n## ", md)[1:]:
        head = block.split("\n", 1)[0].strip()
        out.append((head, len(re.findall(r"^### ", block, flags=re.M))))
    return [s for s in out if s[1]]


def largest_projects(md: str) -> list[dict]:
    """The sample's 'Largest projects' items, as notice-sign data. Everything comes from the markdown."""
    block = next((b for b in re.split(r"\n## ", md) if b.startswith("Largest projects")), "")
    out = []
    for item in re.split(r"\n### ", block)[1:]:
        lines = [x.strip() for x in item.strip().split("\n") if x.strip()]
        title = lines[0]
        council, _, what = title.partition(": ")
        units = re.search(r"(\d[\d,]*)-unit", title)
        meta = next((x.strip("*") for x in lines[1:] if x.startswith("*")), "")
        para = " ".join(x for x in lines[1:] if not x.startswith(("*", "[")))
        link = re.search(r"\[([^\]]+)\]\((https?://[^)]+)\)", item)
        parts = [p.strip() for p in meta.split("·")]
        m = re.match(r"(.*?)\s*(\d{4}-\d{2}-\d{2})", parts[0] if parts else "")
        body, when = (m.group(1).strip(), m.group(2)) if m else (parts[0] if parts else "", "")
        file_ = next((re.sub(r"^Files?\s+", "", p) for p in parts if re.match(r"Files?\s", p)), "")
        text = f"{title} {meta} {para}"
        apps = []
        if re.search(r"\bOPA\b|official plan amendment", text, re.I):
            apps.append("Official plan amendment")
        if re.search(r"\bZBLA\b|zoning by-law amendment|rezoning", text, re.I):
            apps.append("Zoning by-law amendment")
        what = re.sub(r"^\d[\d,]*-unit,?\s*", "", what)
        out.append({"council": council, "short": re.sub(r"^(City|Town|Township|County|Municipality) of ", "", council),
                    "units": units.group(1) if units else "", "what": what[:1].upper() + what[1:], "apps": apps,
                    "body": body, "when": _day(when) if when else "", "file": file_,
                    "src": link.group(1) if link else "", "url": link.group(2) if link else ""})
    return [p for p in out if p["units"]]


# ---------------- live activity (counts only) ----------------

def housing_activity(today: date, excerpts: Path | None = None, days: int = WINDOW_DAYS) -> dict[str, list]:
    """{municipality: [[iso date, meeting name], ...] newest first}: meetings whose documents the housing filter
    flagged, dated from `days` ago onward (including agendas already posted for upcoming meetings)."""
    excerpts = excerpts or ROOT / "data" / "excerpts"
    seen: set = set()
    for f in excerpts.glob("*/housing__*.json"):
        try:
            d = json.loads(f.read_text())
            when = date.fromisoformat((d.get("meeting_date") or "")[:10])
        except (ValueError, OSError):
            continue
        if when < today - timedelta(days=days) or not d.get("municipality"):
            continue
        seen.add((d["municipality"], when.isoformat(), (d.get("meeting_name") or "Meeting").strip()))
    out: dict[str, list] = {}
    for muni, when, name in sorted(seen, key=lambda k: (k[1], k[2]), reverse=True):
        out.setdefault(muni, []).append([when, name])
    return out


def _next_meetings(today: date) -> dict[str, list]:
    try:
        from radar import config, council_pages, tracker
        return {m: [v[0][1][:10], v[0][0]] for m, v in
                council_pages._upcoming(config.DB_PATH, today, tracker._meeting_rank).items() if v}
    except Exception:  # noqa: BLE001  (the page still works without next meetings)
        return {}


def lookup_data(today: date, excerpts: Path | None = None) -> dict:
    act = housing_activity(today, excerpts)
    nxt = _next_meetings(today)
    try:
        names = json.loads((ROOT / "site" / "councils.json").read_text())["councils"]
    except (OSError, ValueError, KeyError):
        names = []
    rows = []
    known = set()
    for c in names:
        n = c["n"]
        known.add(n)
        r = {"n": n, "r": 1 if c.get("c") else 0}
        if n in act:
            r["k"] = len(act[n])
            r["h"] = act[n][:3]
        if n in nxt and r["r"]:
            r["x"] = nxt[n]
        rows.append(r)
    for n, v in act.items():  # a council we read that isn't in councils.json (shouldn't happen)
        if n not in known:
            rows.append({"n": n, "r": 1, "k": len(v), "h": v[:3]})
    return {"built": today.isoformat(), "days": WINDOW_DAYS, "meetings": sum(len(v) for v in act.values()),
            "councils": len(act), "read": sum(1 for r in rows if r["r"]), "rows": rows}


# ---------------- markup ----------------

def notice_sign(projects: list[dict], week: str) -> str:
    if not projects:
        return ""
    tabs = "".join(
        f'<button type="button" class="hs-tab" id="hs-tab-{i}" role="tab" aria-controls="hs-sign-{i}" '
        f'aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}">'
        f'<b>{e(p["units"])}</b> {e(p["short"])}</button>' for i, p in enumerate(projects))
    boards = []
    for i, p in enumerate(projects):
        apps = "".join(f"<li>{e(a)}</li>" for a in p["apps"]) or "<li>Planning application</li>"
        rows = [("What", e(p["what"])), ("Applications", f'<ul class="hs-apps">{apps}</ul>')]
        if p["body"] or p["when"]:
            rows.append(("At council", e(", ".join(x for x in (p["body"], p["when"]) if x))))
        if p["file"]:
            rows.append(("File", e(p["file"])))
        dl = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows)
        src = (f'<a class="hs-src" href="{e(p["url"])}" rel="noopener">Read the {e(p["src"].lower())}</a>'
               if p["url"] else "")
        boards.append(
            f'<div class="hs-board" id="hs-sign-{i}" role="tabpanel" aria-labelledby="hs-tab-{i}"{"" if i == 0 else " hidden"}>'
            f'<p class="hs-head">Development proposal</p>'
            f'<div class="hs-body"><p class="hs-where">{e(p["council"])}</p>'
            f'<p class="hs-units"><span>{e(p["units"])}</span> homes proposed</p>'
            f'<dl>{dl}</dl>{src}</div>'
            f'<p class="hs-foot">From the Council Radar housing sample, {e(week)}</p></div>')
    return (f'<figure class="hs-sign" aria-label="The largest projects in this month\'s sample">'
            f'<div class="hs-tabs" role="tablist" aria-label="Largest projects">{tabs}</div>'
            f'<div class="hs-stand">{"".join(boards)}<span class="hs-post" aria-hidden="true"></span>'
            f'<span class="hs-post" aria-hidden="true"></span></div>'
            f'<figcaption>Real items from public agendas and minutes. Each sign links to the council\'s own document.</figcaption></figure>')


def hero(projects: list[dict], data: dict, secs: list[tuple[str, int]], week: str) -> str:
    total = sum(n for _, n in secs)
    toc = "".join(f'<li><a href="#{_slug(h)}">{e(h)}</a> <span>{n}</span></li>' for h, n in secs)
    proof = (f'In the last {data["days"]} days, plus agendas already posted for coming meetings, the housing filter found '
             f'planning items at <strong>{data["meetings"]} council and committee meetings</strong> across '
             f'<strong>{data["councils"]} of the {data["read"]} councils</strong> we read.') if data["meetings"] else ""
    return f"""
<header class="hs-top"><a class="hs-brand" href="index.html">Council Radar</a>
<nav aria-label="Editions"><a href="index.html">Energy edition</a><a href="housing.html" aria-current="page">Housing edition</a></nav>
<a class="hs-cta-sm" href="{TRIAL}" data-start data-edition="housing">Start free</a></header>
<section class="hs-hero" aria-labelledby="hs-h1">
<div class="hs-copy">
<h1 id="hs-h1">Every rezoning, OPA and subdivision headed to an Ontario council, in one Monday email</h1>
<p class="lede">Council Radar reads the agendas and minutes of {data["read"] or 150} Ontario councils every day. The housing edition
pulls out what builders, developers, planners and land-use lawyers need: official plan and zoning amendments, plans of
subdivision and condominium, site plans, Ontario Land Tribunal settlements, development charges, CIPs and housing-target
funding. Each item links to the council's own document.</p>
<form class="hs-find" id="hs-find" role="search" onsubmit="return false">
<label for="hs-q">See what's on your councils' agendas</label>
<div class="hs-row"><input id="hs-q" list="hs-list" autocomplete="off" placeholder="Type a municipality, e.g. Barrie">
<button type="submit">Check</button></div><datalist id="hs-list"></datalist>
<div id="hs-out" class="hs-out" aria-live="polite"></div>
</form>
<p class="hs-btns"><a class="btn" href="{FOUNDING}">Subscribe for $59 a month</a><a class="btn alt" href="{TRIAL}" data-start data-edition="housing">Get two free trial issues</a></p>
<p class="also">No card needed for the trial. <a href="{TEAM}">Team plan, $249 a month (5 people)</a>. Cancel any time.</p>
</div>
{notice_sign(projects, week)}
</section>
<section class="hs-proof" aria-label="This month">
<p>{proof}</p>
<p class="hs-toc-h">The sample issue below has {total} items:</p>
<ol class="hs-toc">{toc}</ol>
</section>
"""


EXTRA_CSS = """
body{background:var(--mist)}
.hs-top,.hs-hero,.hs-proof{max-width:72rem;margin:0 auto;padding-left:1.5rem;padding-right:1.5rem;box-sizing:border-box}
.hs-top{display:flex;align-items:center;gap:1.5rem;padding-top:1.1rem;padding-bottom:.6rem}
.hs-brand{font:700 1.15rem/1 "Barlow Semi Condensed","Public Sans",sans-serif;color:var(--ink);text-decoration:none}
.hs-top nav{display:flex;gap:1.1rem;margin-left:auto;font-size:.95rem}
.hs-top nav a{color:var(--muted);text-decoration:none;padding:.3rem 0;border-bottom:2px solid transparent}
.hs-top nav a[aria-current]{color:var(--ink);font-weight:600;border-color:var(--ink)}
.hs-cta-sm{font-weight:600;color:var(--ink);text-decoration:none;border:1.5px solid var(--ink);border-radius:8px;padding:.45rem .85rem}
.hs-hero{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,.9fr);gap:3.5rem;align-items:start;padding-top:2.2rem;padding-bottom:2rem}
.hs-hero h1{font:700 clamp(2rem,3.8vw,2.9rem)/1.05 "Barlow Semi Condensed","Public Sans",sans-serif;letter-spacing:-.01em;margin:0 0 1rem;max-width:20ch}
.lede{font-size:1.1rem;color:var(--text);max-width:38rem}
.btn.alt{background:#fff;color:var(--ink);border:1.5px solid var(--ink)}.btn.alt:hover{background:var(--mist);color:var(--ink)}
.btn:focus-visible,.hs-cta-sm:focus-visible,.hs-tab:focus-visible,.hs-find button:focus-visible,.hs-find input:focus-visible{outline:3px solid var(--line);outline-offset:3px}
.also{font-size:.95rem;color:var(--muted);margin-top:.3rem}
.hs-find{margin:1.6rem 0 1.2rem;max-width:34rem}
.hs-find label{display:block;font-weight:600;color:var(--ink);margin-bottom:.4rem}
.hs-row{display:flex;background:#fff;border:2px solid var(--ink);border-radius:10px;padding:.3rem}
.hs-row input{flex:1;min-width:0;border:0;font:inherit;padding:.55rem .7rem;background:transparent;color:var(--text)}
.hs-row input:focus{outline:none}.hs-row:focus-within{box-shadow:0 0 0 3px rgba(47,111,181,.35)}
.hs-row button{font:700 1rem/1 "Public Sans",sans-serif;background:var(--ink);color:#fff;border:0;border-radius:7px;padding:.7rem 1.1rem;cursor:pointer}
.hs-out:empty{display:none}
.hs-out{margin-top:.8rem;background:#fff;border:1px solid var(--rule);border-left:4px solid var(--ink);border-radius:8px;padding:.9rem 1rem}
.hs-out h2{all:unset;display:block;font:700 1.15rem/1.3 "Barlow Semi Condensed","Public Sans",sans-serif;color:var(--ink)}
.hs-out p{margin:.35rem 0;font-size:.95rem}.hs-out ul{margin:.3rem 0 .5rem;padding-left:1.1rem;font-size:.92rem;color:var(--muted)}
.hs-out .btn{margin:.4rem 0 0}
.hs-out .hs-chips{display:flex;flex-wrap:wrap;gap:.4rem;margin:.6rem 0 0;padding:0;list-style:none;font-size:.88rem}
.hs-chips li{background:var(--mist);border-radius:999px;padding:.2rem .7rem;color:var(--ink)}
/* the notice sign */
.hs-sign{margin:0;position:relative}
.hs-tabs{display:flex;gap:.4rem;margin-bottom:.9rem;flex-wrap:wrap}
.hs-tab{font:500 .9rem/1.2 "Public Sans",sans-serif;color:var(--muted);background:transparent;border:1.5px solid var(--rule);border-radius:8px;padding:.45rem .7rem;cursor:pointer}
.hs-tab b{font:700 1rem/1 "Barlow Semi Condensed",sans-serif;color:var(--ink);margin-right:.15rem}
.hs-tab[aria-selected="true"]{background:#fff;border-color:var(--ink);color:var(--ink)}
.hs-stand{position:relative;padding-bottom:4.2rem}
.hs-stand::after{content:"";position:absolute;left:-1rem;right:-1rem;bottom:0;height:10px;border-radius:50%;background:radial-gradient(closest-side,rgba(20,40,75,.18),transparent)}
.hs-post{position:absolute;bottom:.3rem;width:12px;height:5rem;background:linear-gradient(90deg,#9AA6B5,#C9D1DB 45%,#8A97A8);border-radius:2px;z-index:0}
.hs-post:first-of-type{left:18%}.hs-post:last-of-type{right:18%}
.hs-board{position:relative;z-index:1;background:#fff;border:3px solid var(--ink);border-radius:4px;box-shadow:0 18px 40px -24px rgba(20,40,75,.55)}
.hs-board[hidden]{display:none}
.hs-head{margin:0;background:var(--ink);color:#fff;font:700 1.55rem/1 "Barlow Semi Condensed",sans-serif;padding:.8rem 1.1rem;letter-spacing:.01em}
.hs-body{padding:1rem 1.1rem .9rem}
.hs-where{margin:0;font:600 1.05rem/1.2 "Public Sans",sans-serif;color:var(--ink)}
.hs-units{margin:.2rem 0 .6rem;font:600 1.05rem/1 "Public Sans",sans-serif;color:var(--muted)}
.hs-units span{font:700 4.4rem/.95 "Barlow Semi Condensed",sans-serif;color:var(--ink);letter-spacing:-.02em;margin-right:.3rem}
.hs-body dl{display:grid;grid-template-columns:7.2rem 1fr;gap:.35rem .8rem;margin:0;font-size:.92rem;border-top:1px solid var(--rule);padding-top:.7rem}
.hs-body dt{color:var(--muted)}.hs-body dd{margin:0;color:var(--text)}
.hs-apps{margin:0;padding:0;list-style:none}
.hs-src{display:inline-block;margin-top:.8rem;font-weight:600}
.hs-foot{margin:0;border-top:1px solid var(--rule);padding:.5rem 1.1rem;font-size:.8rem;color:var(--muted)}
.hs-sign figcaption{font-size:.85rem;color:var(--muted);margin-top:.2rem}
.hs-proof{padding-top:0;padding-bottom:.5rem}
.hs-proof>p:first-child{max-width:44rem;font-size:1.02rem;border-top:1px solid var(--rule);padding-top:1.4rem;margin:0}
.hs-toc-h{margin:1rem 0 .3rem;color:var(--muted);font-size:.95rem}
.hs-toc{display:flex;flex-wrap:wrap;gap:.5rem;margin:0;padding:0;list-style:none}
.hs-toc li{background:#fff;border:1px solid var(--rule);border-radius:8px;padding:.35rem .7rem;font-size:.92rem}
.hs-toc span{color:var(--muted);margin-left:.2rem}
main{margin-top:1.5rem}
main h2{scroll-margin-top:1rem}
@media (max-width:860px){.hs-hero{grid-template-columns:minmax(0,1fr);gap:2rem;padding-top:1.2rem}.hs-hero h1{max-width:none}
 .hs-top nav a:first-child{display:none}.hs-top nav{gap:.8rem}}
@media (max-width:480px){.hs-units span{font-size:3.6rem}.hs-body dl{grid-template-columns:1fr;gap:.1rem}.hs-body dd{margin-bottom:.4rem}
 .hs-btns .btn{display:block;text-align:center;margin-right:0}.hs-cta-sm{padding:.4rem .65rem;font-size:.9rem;margin-left:auto}.hs-top nav{display:none}}
@media (prefers-reduced-motion:no-preference){.hs-board{animation:hs-up .35s cubic-bezier(.2,.8,.2,1)}}
@keyframes hs-up{from{transform:translateY(8px);opacity:.4}}
"""

PAGE_JS = r"""<script>
(function(){
  "use strict";
  // Notice-sign tabs (arrow keys move between them).
  var tabs=[].slice.call(document.querySelectorAll('.hs-tab'));
  function pick(i,focus){tabs.forEach(function(t,j){var on=i===j;t.setAttribute('aria-selected',on);t.tabIndex=on?0:-1;
    document.getElementById(t.getAttribute('aria-controls')).hidden=!on;});if(focus)tabs[i].focus();}
  tabs.forEach(function(t,i){t.addEventListener('click',function(){pick(i);});
    t.addEventListener('keydown',function(ev){var d=ev.key==='ArrowRight'?1:ev.key==='ArrowLeft'?-1:0;if(d){ev.preventDefault();pick((i+d+tabs.length)%tabs.length,true);}});});
  // Council lookup: counts of meetings with housing items (never their content), next meeting, add to your list.
  var D=JSON.parse(document.getElementById('housing-data').textContent),rows=D.rows,picked=[];
  var esc=function(s){return String(s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});};
  var fold=function(s){return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/[^a-z0-9]+/g,' ').trim();};
  var core=function(n){return fold(n.replace(/^(City|Town|Township|Municipality|County|Village|Region|United Counties|Regional Municipality) of /,'').replace(/ County$/,''));};
  var M='Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(' ');
  var day=function(s){var p=s.split('-');return M[+p[1]-1]+' '+(+p[2]);};
  document.getElementById('hs-list').innerHTML=rows.map(function(r){return '<option value="'+esc(r.n)+'">';}).join('');
  var out=document.getElementById('hs-out'),q=document.getElementById('hs-q');
  function find(v){var f=fold(v);if(!f)return null;
    return rows.filter(function(r){return fold(r.n)===f;})[0]||rows.filter(function(r){return core(r.n)===f;}).sort(function(a,b){return (b.r-a.r)||((b.k||0)-(a.k||0));})[0]
      ||rows.filter(function(r){return fold(r.n).indexOf(f)>-1;}).sort(function(a,b){return (b.k||0)-(a.k||0);})[0]||null;}
  function show(){var r=find(q.value);
    if(!r){out.innerHTML='<p>No Ontario municipality matches "'+esc(q.value)+'". Try the town or city name, e.g. Barrie.</p>';return;}
    if(picked.indexOf(r.n)<0)picked.push(r.n);
    var h='<h2>'+esc(r.n)+'</h2>';
    if(!r.r)h+='<p>We don\'t read this council\'s agendas yet. Ask for it in your trial request and Huxley will cover it by hand for early subscribers.</p>';
    else if(r.k){h+='<p><strong>'+r.k+(r.k===1?' meeting':' meetings')+'</strong> with rezonings, OPAs, subdivisions or other housing items in the last '+D.days+' days and on posted agendas. Most recent:</p><ul>'
      +r.h.map(function(m){return '<li>'+esc(m[1])+', '+day(m[0])+'</li>';}).join('')+'</ul><p>Subscribers get what each item is, the unit counts and the staff recommendation, with links.</p>';}
    else h+='<p>No housing items on this council\'s agendas in the last '+D.days+' days. The Monday email tells you when one appears.</p>';
    if(r.x)h+='<p>Next meeting: '+esc(r.x[1])+', '+day(r.x[0])+'.</p>';
    h+='<a class="btn" href="mailto:councilradaron@gmail.com?subject=Free%20trial%20issue%20-%20Housing" data-start data-edition="housing" data-councils="'+esc(picked.join('|'))+'">Start free with '+(picked.length===1?esc(r.n.replace(/^(City|Town|Township|Municipality|County|Village) of /,'')):picked.length+' councils')+'</a>';
    if(picked.length>1)h+='<ul class="hs-chips" aria-label="Your councils">'+picked.map(function(n){return '<li>'+esc(n)+'</li>';}).join('')+'</ul>';
    out.innerHTML=h;if(window.CRStart&&CRStart.dock)CRStart.dock(picked.length);}
  document.getElementById('hs-find').addEventListener('submit',function(ev){ev.preventDefault();show();});
  q.addEventListener('change',function(){if(find(q.value)&&fold(find(q.value).n)===fold(q.value))show();});
})();
</script>"""


def build(today: date | None = None) -> Path:
    today = today or date.today()
    tpl = (ROOT / "site" / "sample.html").read_text()
    md = (ROOT / "samples" / "housing-sample.md").read_text()
    week = (re.search(r"Week of ([A-Z][a-z]+ \d+, \d{4})", md) or [None, "this month"])[1]
    projects = largest_projects(md)
    secs = sections(md)
    data = lookup_data(today)
    body = markdown.markdown(md).replace("<h1>", "<h2>").replace("</h1>", "</h2>")
    body = re.sub(r"<h2>(.*?)</h2>", lambda m: f'<h2 id="{_slug(html.unescape(m.group(1)))}">{m.group(1)}</h2>', body)
    head, rest = tpl.split('<body><main><a class="back" href="index.html">Back to Council Radar</a>', 1)
    tail = rest[rest.index("</main>"):]
    head = re.sub(r"<title>.*?</title>", "<title>Council Radar Housing: Ontario rezonings, OPAs and subdivisions every Monday</title>", head)
    head = re.sub(r'(<meta property="og:title" content=")[^"]*', r"\1Council Radar Housing: Ontario development decisions every Monday", head)
    head = re.sub(r'(<meta property="og:description" content=")[^"]*',
                  r"\1Rezonings, official plan amendments, subdivisions, OLT settlements and DC changes from 150 Ontario councils, each linked to its source.", head)
    head = head.replace("sample.html", "housing.html").replace("</style>", EXTRA_CSS + "</style>", 1)
    head = re.sub(r'<link href="https://fonts.googleapis.com/css2\?[^"]*" rel="stylesheet">', FONTS, head, count=1)
    # the click-tracking script matches 'sample.html' to label sample views; keep that string intact
    head = head.replace("indexOf('housing.html')", "indexOf('sample.html')")
    if '<meta name="description"' not in head:
        head = head.replace("</title>", '</title><meta name="description" content="Rezonings, OPAs, subdivisions, OLT settlements and development charges from 150 Ontario councils, every Monday, each item linked to its source.">', 1)
    cta = (f'<div class="cta" id="subscribe"><p><strong>Get this every Monday.</strong> Development and housing decisions from '
           f'{data["read"] or 150} Ontario councils, each item linked to its source. Founding rate for the first 25 subscribers.</p>'
           f'<p><a class="btn" href="{FOUNDING}">Subscribe for $59 a month</a> <a href="{TEAM}">Team plan, $249 a month</a> · '
           f'<a href="{TRIAL}" data-start data-edition="housing">Get two free trial issues</a></p>'
           f'<p>Tracking energy projects instead? <a href="sample.html">See the energy edition</a>.</p></div>')
    blob = json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    tail = tail.replace('<script src="start.js"></script>',
                        '<script>window.CRStart={edition:"housing"};</script><script src="start.js"></script>'
                        f'<script type="application/json" id="housing-data">{blob}</script>{PAGE_JS}', 1)
    page = (head + "<body>" + hero(projects, data, secs, week) + "<main>\n" + body + "\n" + cta + tail)
    out = ROOT / "site" / "housing.html"
    out.write_text(page)
    return out


if __name__ == "__main__":
    print(f"wrote {build()}")
