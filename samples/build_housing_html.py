"""Render samples/housing-sample.md into site/housing.html: the Housing feed's landing + sample page.

Built from site/sample.html so it keeps the site's styles, analytics tag and start.js.
Stripe: dedicated 'Council Radar: Ontario Housing' product (prod_Vgjik3VMtFI1Oy) with its own $59 and $249 CAD/month
payment links, created 2026-11-24; still tagged ?client_reference_id=housing.
"""
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
FOUNDING = "https://buy.stripe.com/eVqeVfcwceIv5Ds4Px8Vi02?client_reference_id=housing"
TEAM = "https://buy.stripe.com/4gM00l67O6bZ5DschZ8Vi03?client_reference_id=housing"
TRIAL = "mailto:councilradaron@gmail.com?subject=Free%20trial%20issue%20-%20Housing"

INTRO = f"""
<p class="kicker">New: Council Radar for land development and housing</p>
<h1>Every rezoning, OPA and subdivision headed to an Ontario council, in one Monday email</h1>
<p class="lede">Council Radar reads the agendas and minutes of 150 Ontario councils every day. The housing edition pulls out what builders,
developers, planners and land-use lawyers need: official plan and zoning amendments, plans of subdivision and condominium,
site plans, Ontario Land Tribunal settlements, development charges, CIPs and housing-target funding. Each item links to the
council's own document.</p>
<p><a class="btn" href="{FOUNDING}">Subscribe for $59 a month</a> <a class="btn alt" href="{TEAM}">Team plan, $249 a month (5 people)</a></p>
<p class="also"><a href="{TRIAL}">Get two free trial issues</a> · no card needed · cancel any time</p>
<hr>
"""

CTA = f"""<div class="cta"><p><strong>Get this every Monday.</strong> Development and housing decisions from 150 Ontario councils, each item linked to its source. Founding rate for the first 25 subscribers.</p><p><a class="btn" href="{FOUNDING}">Subscribe for $59 a month</a> <a href="{TEAM}">Team plan, $249 a month</a> · <a href="{TRIAL}">Get two free trial issues</a></p><p>Tracking energy projects instead? <a href="sample.html">See the energy edition</a>.</p></div>"""

EXTRA_CSS = (".kicker{font-weight:600;color:var(--line);text-transform:uppercase;letter-spacing:.06em;font-size:.8rem;margin:1.5rem 0 0}"
             ".lede{font-size:1.1rem;color:var(--text)} .btn.alt{background:#fff;color:var(--ink);border:1px solid var(--ink)}"
             ".also{font-size:.95rem;color:var(--muted)}")


def build() -> Path:
    tpl = (ROOT / "site" / "sample.html").read_text()
    md = (ROOT / "samples" / "housing-sample.md").read_text()
    body = markdown.markdown(md).replace("<h1>", "<h2>").replace("</h1>", "</h2>")
    head, rest = tpl.split('<body><main><a class="back" href="index.html">Back to Council Radar</a>', 1)
    tail = rest[rest.index("</main>"):]
    head = re.sub(r"<title>.*?</title>", "<title>Council Radar Housing: Ontario rezonings, OPAs and subdivisions every Monday</title>", head)
    head = re.sub(r'(<meta property="og:title" content=")[^"]*', r"\1Council Radar Housing: Ontario development decisions every Monday", head)
    head = re.sub(r'(<meta property="og:description" content=")[^"]*',
                  r"\1Rezonings, official plan amendments, subdivisions, OLT settlements and DC changes from 150 Ontario councils, each linked to its source.", head)
    head = head.replace("sample.html", "housing.html").replace("</style>", EXTRA_CSS + "</style>", 1)
    # the click-tracking script matches 'sample.html' to label sample views; keep that string intact
    head = head.replace("indexOf('housing.html')", "indexOf('sample.html')")
    if '<meta name="description"' not in head:
        head = head.replace("</title>", '</title><meta name="description" content="Rezonings, OPAs, subdivisions, OLT settlements and development charges from 150 Ontario councils, every Monday, each item linked to its source.">', 1)
    page = (head + '<body><main><a class="back" href="index.html">Back to Council Radar</a>\n'
            + INTRO + body + "\n" + CTA + tail)
    out = ROOT / "site" / "housing.html"
    out.write_text(page)
    return out


if __name__ == "__main__":
    print(f"wrote {build()}")
