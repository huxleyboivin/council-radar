"""Evergreen guide pages at /guides/<slug>/ plus an index at /guides/.

Written for the searches energy developers, consultants and lawyers actually make ("ieso lt2", "lt2 rfp",
"ieso lt2 results", "solar farms in ontario", "municipal support resolution"), from public IESO tables and
reports. Every fact carries a source link. Built on every deploy (site/guides/ is gitignored) so the
council links and dates stay current. Update the data blocks below when the IESO posts new results or the
final Window 2 documents (expected Q1 2027).
"""
from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

from . import config
from .council_pages import _e, _shell

SITE_URL = config.SITE_URL

# --- Sources -------------------------------------------------------------------------------------------
S = {
    "w2_pres": ("IESO, LT2 RFP Window 2 community engagement presentation (July 8, 2026)",
                "https://ieso.ca/-/media/Files/IESO/Document-Library/engage/long-term-rfp-community/lt2-rfp-window2-community-20260708-presentation.pdf"),
    "e1_table": ("IESO, LT2(e-1) final results with prices (May 8, 2026)",
                 "https://ieso.ca/-/media/Files/IESO/Document-Library/long-term-rfp/energy/LT2e-1-Public-Result-Table-with-Prices-2026-05-08.pdf"),
    "e1_news": ("IESO news: 14 projects selected in the LT2 energy stream (April 10, 2026)",
                "https://ieso.ca/Sector-Participants/IESO-News/2026/04/April-9-IESO-Selects-14-Projects-Through-the-Long-Term-2-Request-for-Proposal-Energy-Stream"),
    "c1_table": ("IESO, LT2(c-1) final results with individual prices (July 13, 2026)",
                 "https://www.ieso.ca/-/media/Files/IESO/Document-Library/long-term-rfp/capacity/LT2c-1-20260702-Public-Result-Table-With-Individual-Prices.pdf"),
    "lt2_page": ("IESO, Long-Term 2 RFP page",
                 "https://www.ieso.ca/Sector-Participants/Resource-Acquisition-and-Contracts/Long-Term-2-RFP"),
    "ottawa_memo": ("City of Ottawa memo on the LT2 procurement (July 4, 2025)",
                    "https://documents.ottawa.ca/sites/default/files/2025%2007%2004%20Memo%20-%20Independent%20Electricity%20Systems%20Operator%20%28IESO%29%20Long%20term%202%20%28LT2%29%20Procurement_EN-AODA.pdf"),
    "ottawa_engage": ("City of Ottawa, IESO LT2 procurement process page",
                      "https://engage.ottawa.ca/independent-electricity-service-operator-ieso-long-term-2-lt2-procurement-process"),
    "amo_toolkit": ("AMO, Municipal Energy Procurement Toolkit (Summer 2025 revisions)",
                    "https://www.amo.on.ca/sites/default/files/assets/DOCUMENTS/Energy/2025/Energy-Procurement-Tool-Kit-Summer-2025-Revisions.pdf"),
    "amo_faq": ("AMO, Energy FAQs on LT2 (January 2025)",
                "https://www.amo.on.ca/sites/default/files/assets/DOCUMENTS/Energy/2025/-ENERGYFAQsonLT2January2025.pdf"),
    "amo_dev": ("AMO, Navigating Municipal Relations: a guide for energy developers (February 2025)",
                "https://amo.on.ca/sites/default/files/assets/DOCUMENTS/Energy/2025/BestPracticesforEnergyDevelopers_20250206Final.pdf"),
    "pembina": ("Pembina Institute, Power Playbook Part 2: Municipal Support Confirmation",
                "https://www.pembina.org/sites/default/files/2025-09/Power-Playbook-Pt2-MSC.pdf"),
    "ieso_form": ("IESO prescribed form: Evidence of Municipal Support (LLT)",
                  "https://ieso.ca/-/media/Files/IESO/Document-Library/long-lead-time/LLT-2026/LLTePFDraftMS100Evidence-of-Municipal-Support.pdf"),
    "taf": ("The Atmospheric Fund, Six Ontario municipalities shine with solar leadership (December 9, 2025)",
            "https://taf.ca/six-ontario-municipalities-shine-with-solar-leadership/"),
    "haldimand": ("Haldimand Press, Haldimand tightens rules for future energy project approvals",
                  "https://haldimandpress.com/haldimand-tightens-rules-for-future-energy-project-approvals/"),
    "richmondhill": ("City of Richmond Hill, staff report SRPBS.26.004 (April 1, 2026)",
                     "https://pub-richmondhill.escribemeetings.com/filestream.ashx?DocumentId=72776"),
    "selwyn": ("Township of Selwyn, Municipal Support Resolution protocol (By-law 2025-049)",
               "https://www.selwyntownship.ca/media/ummlaj4s/selwyn-msr-protocol-final.pdf"),
    "puslinch": ("Wellington Advertiser, Brighter days may be ahead for solar farm project",
                 "https://www.wellingtonadvertiser.com/brighter-days-may-be-ahead-for-solar-farm-project/"),
    "minto": ("Wellington Advertiser, Minto residents hear concerns about proposed wind turbines",
              "https://www.wellingtonadvertiser.com/minto-residents-hear-concerns-about-proposed-wind-turbines/"),
    "wellesley": ("Observer, Mixed reviews for a Wellesley wind turbine proposal",
                  "https://www.observerxtra.com/mixed-reviews-for-a-wellesley-wind-turbine-proposal-still-in-its-early-stages/"),
    "shuniah": ("Energy-Storage.news, Ontario municipality denies support for 3.2GWh BESS project",
                "https://www.energy-storage.news/ontario-municipality-denies-support-for-3-2gwh-bess-project-ahead-of-looming-ieso-rfp-deadline/"),
    "elora": ("Township of Centre Wellington, planning report on the Elora BESS",
              "https://www.centrewellington.ca/media/fg5jxhak/planning-report_elora-bess.pdf"),
    "canrea_lt1": ("CanREA, members successful in Ontario energy storage RFP (May 9, 2024)",
                   "https://renewablesassociation.ca/canrea-members-successful-in-ontario-energy-storage-rfp/"),
    "elt1": ("IESO, E-LT1 RFP selected proponents (September 18, 2023)",
             "https://www.IESO.ca/-/media/Files/IESO/Document-Library/long-term-rfp/ELT1-RFP-Selected-Proponents.pdf"),
    # Nuclear
    "cnsc_dnnp": ("Canadian Nuclear Safety Commission, Darlington New Nuclear Project",
                  "https://www.cnsc-ccsn.gc.ca/eng/reactors/new-reactor-power-plant-projects/new-reactor-power-plant-facilities/darlington-new-nuclear-project/"),
    "power_dnnp": ("POWER Magazine, Ontario authorizes OPG to start construction of first commercial SMR (May 2025)",
                   "https://www.powermag.com/ontario-authorizes-opg-to-start-construction-of-first-commercial-nuclear-smr"),
    "iaac_wes": ("Impact Assessment Agency of Canada, New Nuclear at Wesleyville information session (April 2026)",
                 "https://aeic-iaac.gc.ca/050/documents/p89802/165949E.pdf"),
    "iaac_wes_notice": ("Impact Assessment Agency of Canada, New Nuclear at Wesleyville public notice (January 12, 2026)",
                        "https://iaac-aeic.gc.ca/050/evaluations/document/164781"),
    "opg_wes_letter": ("OPG, Wesleyville community letter (spring 2026)",
                       "https://www.opg.com/documents/wesleyville-community-letter-spring-2026-pdf/"),
    "ans_wes": ("American Nuclear Society, Agreement signed to bring new nuclear to Port Hope (February 17, 2026)",
                "https://www.ans.org/news/2026-02-17/article-7760/agreement-signed-to-bring-worlds-largest-nuclear-station-to-port-hope-ontario/"),
    "bnn_wes": ("BNN Bloomberg, Port Hope's radioactive past fuels pushback against proposed nuclear reactor (August 21, 2026)",
                "https://www.bnnbloomberg.ca/business/2026/08/21/port-hopes-radioactive-past-fuels-pushback-against-proposed-nuclear-reactor/"),
    "cnsc_bruce": ("Canadian Nuclear Safety Commission, Bruce C Nuclear Project",
                   "https://www.cnsc-ccsn.gc.ca/eng/reactors/new-reactor-power-plant-projects/new-reactor-power-plant-facilities/bruce-c-nuclear-project/"),
    "iaac_bruce": ("Impact Assessment Agency of Canada, Bruce C Nuclear Project registry page",
                   "https://www.iaac-aeic.gc.ca/050/evaluations/proj/88771"),
    "iaac_bruce_dec": ("Impact Assessment Agency of Canada, Bruce C notice of impact assessment decision (December 20, 2024)",
                       "https://iaac-aeic.gc.ca/050/evaluations/document/160141"),
    "ieso_w1_overview": ("IESO, Results of the Long-Term 2 Window 1 energy stream (April 2026)",
                         "https://www.ieso.ca/-/media/Files/IESO/Document-Library/long-term-rfp/LT2-W1-results-overview.pdf"),
    # Wind
    "ieso_apr21": ("IESO, LT2 RFP Window 2 engagement presentation (April 21, 2026)",
                   "https://www.ieso.ca/-/media/Files/IESO/Document-Library/engage/long-term-rfp/lt2-rfp-20260421-Presentation.pdf"),
    "ieso_llt_jun": ("IESO, Long Lead-Time RFP community engagement presentation (June 24, 2026)",
                     "https://www.ieso.ca/-/media/Files/IESO/Document-Library/engage/long-term-rfp-community/llt-community-20260624-presentation.pdf"),
    # Agriculture and agrivoltaics
    "omafa_23": ("OMAFA, Guidelines for the LT2 AIA Components Two and Three Requirement",
                 "https://ieso.ca/-/media/Files/IESO/Document-Library/long-term-rfp/lt2-rfp-Guidelines-for-the-LT2-AIA-Components-Two-and-Three-Requirement.pdf"),
    "ieso_aia_qa": ("IESO, Q&A on the LT2 Agricultural Impact Assessment (November 2024)",
                    "https://ieso.ca/-/media/Files/IESO/Document-Library/engage/long-term-rfp/lt2-rfp-AIA-Q-and-A-revised-for-20241126.pdf"),
    "amo_lt2req": ("AMO, LT2 steps and requirements for municipalities",
                   "https://www.amo.on.ca/sites/default/files/assets/DOCUMENTS/Energy/2025/LT2%20Requirements%20for%20Municipalities%20Final.pdf"),
    # Integrated Energy Plan and the IESO
    "iep_page": ("Ontario, Energy for Generations: Ontario's Integrated Plan to Power the Strongest Economy in the G7",
                 "https://ontario.ca/page/energy-generations"),
    "iep_oic": ("Ontario, Order in Council 801/2025 approving the Integrated Energy Plan (June 11, 2025)",
                "https://www.ontario.ca/orders-in-council/oc-8012025"),
    "iep_ieso_dir": ("Ontario, Minister's Directive to the IESO implementing the Integrated Energy Plan (O.C. 803/2025)",
                     "https://www.ontario.ca/page/schedule-order-council-8032025"),
    "iep_ieso_news": ("IESO, Ontario's Integrated Energy Plan outlines new actions (June 12, 2025)",
                      "https://ieso.ca/Sector-Participants/IESO-News/2025/06/Ontarios-Integrated-Energy-Plan-Outlines"),
    "blakes_iep": ("Blakes, Ontario releases Energy for Generations (June 17, 2025)",
                   "https://www.blakes.com/insights/ontario-releases-energy-for-generations-the-province-s-inaugural-integrated-energy-plan/"),
    "torys_iep": ("Torys, Ontario's Integrated Energy Plan: priorities for the next 25 years (July 3, 2025)",
                  "https://www.torys.com/our-latest-thinking/publications/2025/07/on-integrated-energy-plan"),
    "mccarthy_iep": ("McCarthy Tétrault, Planning for Power: overview of Ontario's Integrated Energy Plan",
                     "https://www.mccarthy.ca/en/insights/blogs/canadian-energy-perspectives/planning-for-power-overview-of-ontario-s-integrated-energy-plan"),
    "ngps_ero": ("Environmental Registry of Ontario, Natural Gas Policy Statement (ERO 019-9501)",
                 "https://ero.ontario.ca/node/13353"),
    "mep_ero": ("Environmental Registry of Ontario, Review of the Municipal Energy Plan grant program",
                "https://ero.ontario.ca/node/16241"),
    "ola_estimates": ("Legislative Assembly of Ontario, Standing Committee on the Interior: Ministry of Energy and Mines estimates (September 29, 2026)",
                      "https://www.ola.org/en/legislative-business/committees/interior/parliament-44/transcripts/committee-transcript-2026-sept-29"),
    "oic_rae": ("Ontario, Order in Council 1281/2026 (September 10, 2026)",
                "https://www.ontario.ca/orders-in-council/oc-12812026"),
    "ieso_municipal": ("IESO, LT2 RFP webinar for Indigenous communities and municipalities (July 17, 2025)",
                       "https://www.ieso.ca/-/media/Files/IESO/Document-Library/engage/long-term-rfp-community/lt2rfp-community-20250717-presentation-municipal-session.pdf"),
    "ieso_corp": ("IESO, Corporate IESO: regulatory accountability", "https://ieso.ca/Corporate-IESO"),
    "elec_act": ("Electricity Act, 1998 (Ontario)", "https://www.ontario.ca/laws/statute/98e15"),
    "dbrs_ieso": ("Morningstar DBRS, Independent Electricity System Operator issuer profile",
                  "https://dbrs.morningstar.com/issuers/6599/independent-electricity-system-operator"),
    "opg_smr": ("OPG, OPG ready to begin building North America's first small modular reactor (May 2025)",
                "https://www.opg.com/story/opg-ready-to-begin-building-north-americas-first-small-modular-reactor"),
    "opg_newnuclear": ("OPG, Darlington New Nuclear Project", "https://opg.com/newnuclear"),
    "cbc_smr": ("CBC News, Ontario set to begin construction of Canada's 1st mini nuclear power plant (May 2025)",
                "https://www.cbc.ca/lite/story/1.7529338"),
    "opg_wes_council": ("OPG, Exploring new nuclear in Port Hope: council update (April 21, 2026)",
                        "https://www.opg.com/documents/wesleyville-presentation-to-port-hope-council-april-2026-pdf/"),
    "agv_canada": ("Agrivoltaics Canada, response to Ontario's Affordable Energy Future (December 2024)",
                   "https://ero.ontario.ca/public/public_uploads/2024-12/Agrivoltaics%20Canada%20-%20Response%20to%20Ontario%27s%20Affordable%20Energy%20Future.pdf"),
}

# --- IESO LT2 Window 1 results (final tables) ------------------------------------------------------------
# (municipality as the IESO lists it, council page name if we have one, project, proponent, source, MW, zone, price)
ENERGY_W1 = [
    ("Crown land", None, "Dunns Valley Solar", "Dunns Valley Solar Inc.", "Solar", 200.00, "Northeast", 71.74),
    ("Unorganized District of Thunder Bay (Crown land)", None, "Northern Breeze Wind Project", "Northern Breeze Wind Project Inc.", "Wind", 200.00, "Northwest", 94.95),
    ("Unincorporated territory, Rainy River District", None, "CarbonFree Fort Frances", "CarbonFree Fort Frances Ltd.", "Solar", 167.20, "Northwest", 83.95),
    ("Unincorporated territory, Algoma District", None, "CarbonFree Kynoch", "CarbonFree Kynoch Ltd.", "Solar", 154.00, "Northeast", 86.95),
    ("Township of Sables-Spanish Rivers", None, "Massey Solar", "Massey Solar Inc.", "Solar", 141.25, "Northeast", 93.75),
    ("Township of Chapple", None, "CarbonFree Rainy River", "CarbonFree Rainy River Ltd.", "Solar", 60.00, "Northwest", 99.90),
    ("Town of Fort Frances", None, "Fort Frances Solar", "Fort Frances Solar LP", "Solar", 57.20, "Northwest", 94.88),
    ("Unincorporated territory, District of Timiskaming", None, "Paradis Bay Solar", "Neoen Ontario Solar 3 Inc.", "Solar", 50.00, "Northeast", 96.51),
    ("City of Timmins", None, "Timmins Mountjoy Solar Project", "Timmins Mountjoy Solar LP", "Solar", 23.90, "Northeast", 97.50),
    ("County of Prince Edward", None, "Elmbrook Agrivoltaics", "Elmbrook Agrivoltaics Inc.", "Solar", 19.20, "East", 89.72),
    ("Municipality of West Grey", "Municipality of West Grey", "Cedar Agrivoltaics", "Hanover Agrivoltaics Inc.", "Solar", 17.60, "Southwest", 89.50),
    ("Township of Chatsworth", "Township of Chatsworth", "Chatsworth Solar Project", "Numbered Ontario corporation", "Solar", 15.75, "Southwest", 98.75),
    ("Township of Drummond/North Elmsley", None, "Golden Leaf Agrivoltaics", "Golden Leaf Agrivoltaics Inc.", "Solar", 9.00, "East", 94.50),
]
CAPACITY_W1 = [
    ("Town of Greater Napanee", None, "Napanee Battery Energy Storage System Phase 2", "Napanee BESS Phase 2 Inc.", "Battery storage", 300.00, "East", 527.20),
    ("Unincorporated territory, District of Kenora", None, "Eagle Lake Power Reserve", "Neoen Ontario BESS 2 Inc.", "Battery storage", 190.00, "Northwest", 580.50),
    ("Norfolk County", "County of Norfolk", "Simcoe Battery Project", "Simcoe Battery Project GP Inc.", "Battery storage", 150.00, "Southwest", 614.47),
]

GUIDE_CSS = """
.prose{max-width:46rem}.prose p,.prose li{max-width:44rem}
.prose h2{margin-top:2.2rem}.prose h3{font:700 1.05rem/1.35 "Public Sans",sans-serif;color:var(--ink);margin:1.4rem 0 .3rem}
.tbl{width:100%;border-collapse:collapse;font-size:.92rem;margin:.6rem 0 1rem}
.tbl th,.tbl td{text-align:left;padding:.5rem .55rem;border-bottom:1px solid var(--line);vertical-align:top}
.tbl th{font-weight:700;color:var(--ink);background:var(--mist)}.tbl td.n,.tbl th.n{text-align:right;white-space:nowrap}
.scroll{overflow-x:auto}.tbl .m{display:block;color:var(--muted);font-size:.84rem}
.keyfacts{display:grid;grid-template-columns:repeat(auto-fit,minmax(12rem,1fr));gap:.7rem;margin:1rem 0 1.4rem}
.sources{font-size:.88rem;color:var(--muted)}.sources li{margin:.25rem 0}
.cta{background:var(--ink);color:#C9D4E6;border-radius:12px;padding:1.2rem 1.3rem;margin:2rem 0}.cta strong{color:#fff}
.cta .btn{margin:.6rem .6rem 0 0}.cta .btn.primary{background:#fff;color:var(--ink);border-color:#fff}.cta .btn.secondary{background:transparent;color:#fff;border-color:#8FA3C3}
.guides{list-style:none;padding:0;margin:0}.guides li{padding:1rem 0;border-bottom:1px solid var(--line)}
.guides a{font-weight:700;font-size:1.1rem}.guides p{margin:.2rem 0 0;color:var(--muted)}
"""


def _src(*keys: str) -> str:
    return " ".join(f'<a href="{_e(S[k][1])}" rel="nofollow">[source]</a>' for k in keys)


def _sources(*keys: str) -> str:
    items = "".join(f'<li><a href="{_e(S[k][1])}" rel="nofollow">{_e(S[k][0])}</a></li>' for k in keys)
    return f'<h2>Sources</h2><ul class="sources">{items}</ul>'


def _cta(root: str, councils: str = "") -> str:
    return (f'<div class="cta"><p><strong>Know where each council stands before you submit.</strong> Council Radar reads the agendas, '
            f'staff reports and minutes of 150 Ontario councils every morning and sends one email each Monday: support requests, '
            f'decisions, new rules and zoning changes, each with a source link.</p>'
            f'<a class="btn primary" href="mailto:councilradaron@gmail.com?subject=Free%20trial%20issue" data-start data-councils="{_e(councils)}">Get a free trial issue</a>'
            f'<a class="btn secondary" href="{root}sample.html">Read a sample issue</a></div>')


def _muni(name: str, page_name: str | None, slugs: dict[str, str], root: str) -> str:
    slug = slugs.get(page_name or name)
    return f'<a href="{root}councils/{slug}/">{_e(name)}</a>' if slug else _e(name)


def _page(slug: str, title: str, desc: str, h1: str, lede: str, body: str, today: date, root: str = "../../",
          crumb: str | None = None, faq: list[tuple[str, str]] | None = None) -> str:
    canonical = f"{SITE_URL}guides/{slug}/"
    crumbs = (f'<p class="crumbs"><a href="{root}index.html">Home</a> › <a href="{root}guides/">Guides</a> › {_e(crumb or h1)}</p>')
    main = (f'<main class="prose">{crumbs}<h1>{_e(h1)}</h1><p class="lede">{lede}</p>'
            f'<p class="crumbs">Updated {today.strftime("%B %-d, %Y")} · From public IESO and municipal records</p>{body}</main>')
    graph = [{"@type": "Article", "headline": h1, "description": desc, "dateModified": today.isoformat(),
              "author": {"@type": "Organization", "name": "Council Radar"}, "mainEntityOfPage": canonical},
             {"@type": "BreadcrumbList", "itemListElement": [
                 {"@type": "ListItem", "position": 1, "name": "Council Radar", "item": SITE_URL},
                 {"@type": "ListItem", "position": 2, "name": "Guides", "item": SITE_URL + "guides/"},
                 {"@type": "ListItem", "position": 3, "name": crumb or h1, "item": canonical}]}]
    if faq:
        graph.append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]})
    html_ = _shell(title, desc, canonical, root, main, {"@context": "https://schema.org", "@graph": graph},
                   image=SITE_URL + "og/home.png")
    return html_.replace("</style>", GUIDE_CSS + "</style>", 1)


def _faq_html(faq: list[tuple[str, str]]) -> str:
    return "<h2>Common questions</h2>" + "".join(f"<h3>{_e(q)}</h3><p>{_e(a)}</p>" for q, a in faq)


# --- Pages -----------------------------------------------------------------------------------------------

def lt2_window_2(today: date, slugs: dict, timeline: dict | None) -> str:
    root = "../../"
    rows = [("Final LT2 Window 2 RFP and contract posted", "Q1 2027"),
            ("Pre-engagement with each municipality", "Before submission; in Window 1, at least 60 days before proposals were due"),
            ("Final Deliverability Guidance", "By July 2027"),
            ("Proposals due, each with municipal support", "Q2/Q3 2027"),
            ("Contracts awarded", "Q1 2028"),
            ("Projects in commercial operation", "2032")]
    table = "".join(f"<tr><td>{_e(a)}</td><td>{_e(b)}</td></tr>" for a, b in rows)
    faq = [("When are LT2 Window 2 proposals due?",
            "The IESO's July 2026 timeline puts proposal submission in Q2/Q3 2027, after the final RFP in Q1 2027. Dates are approximate until the final documents are posted."),
           ("Does LT2 Window 2 still need municipal support?",
            "Yes. The IESO says the mandatory municipal support requirement isn't expected to change for any Window 2 proposal, including repowering. Proponents must have the Municipal Support Confirmation before they submit."),
           ("Can existing wind and solar farms bid in Window 2?",
            "Yes, for the first time. Window 2 allows repowering of existing facilities over 1 MW that meet the IESO's eligibility paths, for new 20-year contracts."),
           ("What is the IESO, and is it part of the government?",
            "The Independent Electricity System Operator runs Ontario's grid and buys new supply through procurements like LT2. It's a "
            "not-for-profit corporation set up under the Electricity Act, 1998, under the jurisdiction of Ontario's Minister of Energy. "
            "The Act says it isn't a Crown agent, but the province appoints its board and the minister can issue it directives.")]
    body = f"""
<div class="keyfacts">
<div class="stat"><strong>Q2/Q3 2027</strong><span>proposals due, approximate</span></div>
<div class="stat"><strong>1–3 TWh</strong><span>preliminary energy target</span></div>
<div class="stat"><strong>Mandatory</strong><span>municipal support at submission</span></div>
</div>
<p>LT2 Window 2 is the second round of the IESO's Long-Term 2 procurement, which offers 20-year contracts for new electricity supply in Ontario. The key difference from most procurements: <strong>no project on municipal land can bid without a support resolution from that council</strong>, and the councils elected on October 26, 2026 will make those decisions. {_src("w2_pres")}</p>

<h2>Window 2 timeline</h2>
<p>The IESO's dates are approximate and depend on Ministry direction and the final postings. {_src("w2_pres")}</p>
<div class="scroll"><table class="tbl"><thead><tr><th>Milestone</th><th>Expected</th></tr></thead><tbody>{table}</tbody></table></div>
<p>Stakeholders asked for at least 6 months between the final Deliverability Guidance and the proposal deadline. On the current schedule those two dates are close together, so the deadline may move. {_src("w2_pres")} Add the dates to your calendar: <a href="{root}cal/lt2-window-2.ics">Window 2 calendar feed</a>.</p>

<h2>What's changing from Window 1</h2>
<ul>
<li><strong>A bigger energy target.</strong> The preliminary target is 1–3 TWh. It rises to cover Window 1's shortfall of about 628 GWh, left when one selected proponent didn't sign its contract. {_src("w2_pres")}</li>
<li><strong>Repowering is allowed.</strong> Existing facilities over 1 MW can rebuild or upgrade and compete for a new 20-year contract, if they meet one of two eligibility paths tied to their current contracts and years in service. {_src("w2_pres")}</li>
<li><strong>Location points.</strong> Window 1 gave rated points to Northern Ontario sites. The IESO is exploring more northern capacity, and points for projects on circuits with spare transmission capacity or a local system benefit. {_src("w2_pres")}</li>
<li><strong>Domestic content.</strong> Window 2 will likely let proponents commit to Canadian sourcing for up to a 3% reduction in evaluated price, as in the Long Lead-Time RFP. {_src("w2_pres")}</li>
<li><strong>Agricultural land.</strong> Ground-mounted solar remains barred from prime agricultural areas, and the IESO is reviewing how the Agricultural Impact Assessment applies to repowered sites. {_src("w2_pres", "ottawa_memo")}</li>
</ul>

<h2>What isn't changing: municipal support</h2>
<p>The mandatory municipal support requirement applies to every Window 2 proposal, including repowering. Proponents are responsible for working with the local municipality, including on what the 2026 election means for timing, and must have the Municipal Support Confirmation before they submit. {_src("w2_pres")} A project without its municipality's support at submission isn't eligible for a contract. {_src("ottawa_memo")}</p>
<p>Developers can start talking to municipalities before the final RFP is posted. {_src("w2_pres")} In practice, that means getting on new councils' agendas in the first months of 2027. See <a href="{root}guides/municipal-support-resolution/">how municipal support resolutions work</a> and <a href="{root}guides/where-ontario-councils-stand/">where Ontario councils stand</a>.</p>

<h2>How Window 1 went</h2>
<p>The energy stream ended with 13 contracts, 12 solar and 1 wind, for 2.37 TWh a year, against a 3.0 TWh target. The capacity stream met its 600 MW target with 640 MW of battery storage in 3 contracts. Both streams were heavily oversubscribed: about 4 times in energy and 12 times in capacity. {_src("w2_pres")} See every project and its municipality: <a href="{root}guides/lt2-window-1-results/">LT2 Window 1 results by municipality</a>.</p>

<h2>Who runs LT2: the IESO</h2>
<p>The IESO is a not-for-profit corporate entity established under the Electricity Act, 1998, under the jurisdiction of Ontario's Minister of Energy; the Ontario Energy Board sets its fees and licences. {_src("ieso_corp")} The Act states that the IESO isn't a Crown agent {_src("elec_act")}, and the province appoints its board of directors. {_src("dbrs_ieso")} The minister directs it through formal directives: the LT2 procurement itself started with one. See <a href="{root}guides/ontario-integrated-energy-plan/">Ontario's Integrated Energy Plan</a>.</p>
{_faq_html(faq)}
{_cta(root)}
{_sources("w2_pres", "lt2_page", "ottawa_memo", "ieso_corp", "elec_act", "dbrs_ieso")}"""
    return _page("lt2-window-2", "IESO LT2 Window 2 (2027): dates, rules and municipal support",
                 "LT2 Window 2 timeline, what's changing from Window 1 (repowering, targets, domestic content) and why every proposal still needs council support. Updated from IESO documents.",
                 "IESO LT2 Window 2: dates, rules and municipal support",
                 "When LT2 Window 2 proposals are due, what's new compared with Window 1, and why each Ontario council's support decides which projects can bid.",
                 body, today, crumb="LT2 Window 2", faq=faq)


def _results_table(rows, slugs, root, unit: str) -> str:
    out = []
    for muni, page, project, prop, tech, mw, zone, price in rows:
        out.append(f"<tr><td>{_muni(muni, page, slugs, root)}</td><td>{_e(project)}<br><span class='m'>{_e(prop)}</span></td>"
                   f"<td>{_e(tech)}</td><td class='n'>{mw:,.2f}</td><td>{_e(zone)}</td><td class='n'>${price:,.2f}</td></tr>")
    return (f'<div class="scroll"><table class="tbl"><thead><tr><th>Municipality or location</th><th>Project and proponent</th>'
            f'<th>Type</th><th class="n">MW</th><th>Zone</th><th class="n">{unit}</th></tr></thead><tbody>{"".join(out)}</tbody></table></div>')


def lt2_window_1_results(today: date, slugs: dict, timeline) -> str:
    root = "../../"
    e_mw = sum(r[5] for r in ENERGY_W1)
    north = sum(r[5] for r in ENERGY_W1 if r[6] in ("Northwest", "Northeast"))
    south = [r for r in ENERGY_W1 if r[6] not in ("Northwest", "Northeast")]
    c_mw = sum(r[5] for r in CAPACITY_W1)
    in_muni = [r for r in ENERGY_W1 + CAPACITY_W1 if r[0].startswith(("Township", "Town", "City", "County", "Municipality", "Norfolk"))]
    faq = [("How many projects won LT2 Window 1?",
            f"{len(ENERGY_W1)} energy projects ({e_mw:,.1f} MW, 12 solar and 1 wind) signed contracts in the energy stream, and "
            f"{len(CAPACITY_W1)} battery storage projects ({c_mw:,.0f} MW) won the capacity stream."),
           ("Which municipalities host LT2 Window 1 projects?",
            "Municipalities named in the IESO's final tables include " + ", ".join(sorted({r[0] for r in in_muni})) +
            ". Several northern projects are on Crown land or unincorporated territory."),
           ("What did LT2 Window 1 projects cost?",
            "The IESO reports a weighted average of $88.84/MWh for the energy stream and $563.48/MW-business day for the capacity stream.")]
    body = f"""
<div class="keyfacts">
<div class="stat"><strong>{len(ENERGY_W1)}</strong><span>energy contracts, {e_mw:,.1f} MW</span></div>
<div class="stat"><strong>{len(CAPACITY_W1)}</strong><span>battery contracts, {c_mw:,.0f} MW</span></div>
<div class="stat"><strong>{north / e_mw:.0%}</strong><span>of energy MW in the north</span></div>
</div>
<p>Every LT2 Window 1 contract went to a project with at least 50% Indigenous participation, and most of the energy capacity went north. In the south, only {len(south)} small solar projects won, each under 20 MW, in {", ".join(_muni(r[0], r[1], slugs, root) for r in south)}. {_src("e1_table", "c1_table")}</p>

<h2>Energy stream (LT2(e-1)): solar and wind</h2>
<p>In April 2026 the IESO offered contracts to 14 projects: 12 solar and 2 wind. {_src("e1_news")} One selected proponent didn't sign its contract, leaving 13 projects and a shortfall of about 628 GWh a year, which carries into Window 2. {_src("w2_pres")} The weighted average price was $88.84/MWh: $86.71 for solar and $94.95 for wind. {_src("e1_table")}</p>
{_results_table(ENERGY_W1, slugs, root, "$/MWh")}

<h2>Capacity stream (LT2(c-1)): battery storage</h2>
<p>Three battery storage projects won 20-year contracts for {c_mw:,.0f} MW, above the 600 MW target, at a weighted average of $563.48/MW-business day. Proposals also included natural gas, bioenergy and combined heat and power; the stream was about 12 times oversubscribed. {_src("c1_table", "w2_pres")}</p>
{_results_table(CAPACITY_W1, slugs, root, "$/MW-day")}

<h2>What the results mean for Window 2</h2>
<ul>
<li><strong>Council support was the first filter.</strong> Every project in these tables that sits in a municipality had that council's support at submission. Councils that said no, like <a href="{root}councils/{slugs.get('Municipality of Shuniah', 'municipality-of-shuniah')}/">Shuniah</a> on a 400 MW storage project, kept those projects out of the competition. {_src("shuniah")}</li>
<li><strong>Southern projects were small.</strong> The southern winners were all agrivoltaic or small solar projects under 20 MW. {_src("e1_table")} See <a href="{root}guides/agrivoltaics-ontario/">agrivoltaics in Ontario</a>.</li>
<li><strong>The Window 2 target is larger.</strong> It covers the Window 1 shortfall, and repowered projects can compete. See the <a href="{root}guides/lt2-window-2/">LT2 Window 2 guide</a>.</li>
</ul>
{_faq_html(faq)}
{_cta(root)}
{_sources("e1_table", "e1_news", "c1_table", "w2_pres", "shuniah")}"""
    return _page("lt2-window-1-results", "IESO LT2 Window 1 results by municipality (energy & capacity)",
                 "Every IESO LT2 Window 1 contract (energy and capacity streams) with its municipality, MW, zone and price, from the IESO's final result tables.",
                 "IESO LT2 Window 1 results by municipality",
                 "Every project that won an LT2 Window 1 contract, the municipality it's in, its size and its price, from the IESO's final tables.",
                 body, today, crumb="LT2 Window 1 results", faq=faq)


def municipal_support(today: date, slugs: dict, timeline) -> str:
    root = "../../"

    def m(name):
        return _muni(name, name, slugs, root)
    faq = [("What is a municipal support resolution?",
            "A council resolution confirming that a municipality supports an energy project's proposal to the IESO. Under LT2, a project within a municipality's boundaries can't be submitted without one."),
           ("What is the difference between an MRSPS and a blanket resolution?",
            "A Municipal Resolution in Support of Proposal Submission (MRSPS) supports one specific project. A blanket resolution supports every project that meets criteria the council sets. Both count as a Municipal Support Confirmation."),
           ("Is there a template for a municipal support resolution?",
            "AMO's Municipal Energy Procurement Toolkit lists the mandatory elements of a resolution in an appendix, and the IESO publishes the prescribed Evidence of Municipal Support form for each procurement.")]
    body = f"""
<p>Under the IESO's Long-Term 2 (LT2) procurement, an energy project inside a municipality's boundaries needs that council's support before the developer can submit a proposal. If the municipality doesn't support it at submission, the project isn't eligible for a contract. {_src("ottawa_memo", "amo_faq")} That makes each council's process, timing and politics part of every project's critical path.</p>

<h2>The two kinds of support</h2>
<div class="scroll"><table class="tbl"><thead><tr><th>Type</th><th>What it covers</th><th>When councils use it</th></tr></thead><tbody>
<tr><td><strong>MRSPS</strong> (Municipal Resolution in Support of Proposal Submission)</td><td>One named project</td><td>Council wants to weigh each project, its site and its community engagement</td></tr>
<tr><td><strong>Blanket resolution</strong></td><td>Every project that meets the council's criteria</td><td>Council wants a faster, predictable path, often with authority delegated to staff</td></tr>
</tbody></table></div>
<p>Both are forms of Municipal Support Confirmation (MSC). {_src("pembina")} The developer submits the council's decision to the IESO on a prescribed Evidence of Municipal Support form. {_src("ieso_form")}</p>

<h2>How the process usually runs</h2>
<ol>
<li><strong>Pre-engagement.</strong> The developer contacts the municipality before submitting. In Window 1, pre-engagement had to be confirmed at least 60 days before proposals were due. {_src("ottawa_engage")}</li>
<li><strong>Community engagement.</strong> The developer holds the public meetings the IESO and the council require. {_src("pembina")}</li>
<li><strong>Staff report and council vote.</strong> Staff review the request against the council's protocol and recommend support, refusal or deferral. {_src("pembina")}</li>
<li><strong>Submission.</strong> The resolution goes into the proposal. Projects that later win still need permits, approvals and often zoning. {_src("amo_faq")}</li>
</ol>

<h2>How Ontario councils are handling it</h2>
<div class="scroll"><table class="tbl"><thead><tr><th>Council</th><th>Approach</th><th>Source</th></tr></thead><tbody>
<tr><td>{m("Haldimand County")}</td><td>Kept blanket support and let the CAO issue support letters to projects that meet its criteria. Wind isn't eligible, and a community benefit agreement of $1,133/MW a year applies.</td><td>{_src("haldimand")}</td></tr>
<tr><td>{m("City of Richmond Hill")}</td><td>Staff proposed a blanket resolution with delegated authority for solar, and individual council votes for other technologies.</td><td>{_src("richmondhill")}</td></tr>
<tr><td>{m("Township of Selwyn")}</td><td>Adopted a written protocol setting out what proponents must provide with a support request.</td><td>{_src("selwyn")}</td></tr>
<tr><td>{m("Township of Puslinch")}</td><td>Acknowledged a 7 MW solar project without supporting it, and asked staff for an IESO protocol in Q1 2027.</td><td>{_src("puslinch")}</td></tr>
<tr><td>{m("City of Ottawa")}</td><td>Runs a stepped LT2 process and granted a Municipal Support Confirmation to a battery project on December 10, 2025.</td><td>{_src("ottawa_engage")}</td></tr>
<tr><td>{m("Municipality of Shuniah")}</td><td>Voted against support for a 400 MW, 3.2 GWh storage project before the capacity deadline.</td><td>{_src("shuniah")}</td></tr>
</tbody></table></div>
<p>More decisions as they're confirmed: the <a href="{root}tracker.html">municipal support tracker</a>.</p>

<h2>Templates and guidance</h2>
<ul>
<li><a href="{_e(S["amo_toolkit"][1])}" rel="nofollow">AMO's Municipal Energy Procurement Toolkit</a> lists the mandatory elements of a resolution and options for blanket resolutions.</li>
<li><a href="{_e(S["amo_dev"][1])}" rel="nofollow">AMO's guide for energy developers</a> covers what councils, staff and residents expect.</li>
<li><a href="{_e(S["pembina"][1])}" rel="nofollow">Pembina Institute's Power Playbook</a> explains the Municipal Support Confirmation step by step.</li>
</ul>
{_faq_html(faq)}
{_cta(root)}
{_sources("ottawa_memo", "amo_faq", "pembina", "ieso_form", "ottawa_engage", "amo_toolkit", "amo_dev", "haldimand", "richmondhill", "selwyn", "puslinch", "shuniah")}"""
    return _page("municipal-support-resolution", "Municipal support resolutions (MSC) for IESO projects in Ontario",
                 "What a municipal support resolution (MSC) is, MRSPS versus blanket resolutions, how the process runs, and how Ontario councils like Haldimand, Richmond Hill and Selwyn handle it.",
                 "Municipal support resolutions for IESO energy projects",
                 "What a municipal support resolution is, the two kinds, how councils decide, and how Ontario councils are handling requests for LT2.",
                 body, today, crumb="Municipal support resolutions", faq=faq)


def solar_battery(today: date, slugs: dict, timeline) -> str:
    root = "../../"

    def m(name):
        return _muni(name, name, slugs, root)
    solar = [r for r in ENERGY_W1 if r[4] == "Solar"]
    s_rows = "".join(f"<tr><td>{_muni(r[0], r[1], slugs, root)}</td><td>{_e(r[2])}</td><td class='n'>{r[5]:,.2f}</td></tr>" for r in solar)
    b_rows = "".join(f"<tr><td>{_muni(r[0], r[1], slugs, root)}</td><td>{_e(r[2])}</td><td class='n'>{r[5]:,.0f}</td></tr>" for r in CAPACITY_W1)
    faq = [("How many solar farms won IESO contracts in LT2?",
            f"{len(solar)} solar projects totalling {sum(r[5] for r in solar):,.1f} MW signed LT2 Window 1 contracts, most of them in Northern Ontario."),
           ("Can solar farms be built on farmland in Ontario?",
            "Not on prime agricultural land: the province bars ground-mounted solar in prime agricultural areas for these procurements. Agrivoltaic projects on other land did win LT2 contracts."),
           ("Where are Ontario's new battery storage projects?",
            "LT2 Window 1 contracted battery projects in Greater Napanee, Norfolk County and the District of Kenora. Earlier procurements (E-LT1 in 2023 and LT1 in 2024) contracted more storage across the province.")]
    body = f"""
<p>Ontario is adding solar and battery storage through the IESO's competitive procurements, and every project inside a municipality needs that council's support to bid. This page lists the projects with IESO contracts from LT2 Window 1 and the council decisions we've confirmed on others. {_src("e1_table", "c1_table")}</p>

<h2>Solar farms with LT2 contracts</h2>
<p>{len(solar)} solar projects, {sum(r[5] for r in solar):,.1f} MW in total, signed 20-year contracts in April–May 2026. The four southern projects are agrivoltaic or small solar, each under 20 MW. {_src("e1_table")} More: <a href="{root}guides/agrivoltaics-ontario/">agrivoltaics in Ontario</a>.</p>
<div class="scroll"><table class="tbl"><thead><tr><th>Municipality or location</th><th>Project</th><th class="n">MW</th></tr></thead><tbody>{s_rows}</tbody></table></div>
<p>Ground-mounted solar isn't allowed in prime agricultural areas under these procurements. {_src("ottawa_memo")} Prices and proponents: <a href="{root}guides/lt2-window-1-results/">LT2 Window 1 results</a>.</p>

<h2>Battery storage projects with LT2 contracts</h2>
<div class="scroll"><table class="tbl"><thead><tr><th>Municipality or location</th><th>Project</th><th class="n">MW</th></tr></thead><tbody>{b_rows}</tbody></table></div>
<p>These follow two earlier storage procurements: E-LT1 in 2023 (881.7 MW of storage) and LT1 in 2024 (10 battery facilities, 1,784 MW). {_src("elt1", "canrea_lt1")}</p>

<h2>Proposals and council decisions</h2>
<div class="scroll"><table class="tbl"><thead><tr><th>Council</th><th>Project</th><th>Decision</th><th>Source</th></tr></thead><tbody>
<tr><td>{m("City of Ottawa")}</td><td>West Capital Power battery project (Capital Power)</td><td>Support granted, December 10, 2025</td><td>{_src("ottawa_engage")}</td></tr>
<tr><td>{m("Municipality of Shuniah")}</td><td>400 MW / 3.2 GWh storage (PowerBank)</td><td>Support refused, December 2025</td><td>{_src("shuniah")}</td></tr>
<tr><td>{m("Township of Centre Wellington")}</td><td>Elora BESS (Aypa Power)</td><td>Support letter issued, December 2023</td><td>{_src("elora")}</td></tr>
<tr><td>{m("Township of Puslinch")}</td><td>7 MW solar</td><td>Acknowledged, not supported yet; protocol due Q1 2027</td><td>{_src("puslinch")}</td></tr>
<tr><td>{m("Town of Minto")}</td><td>24 MW solar and 70 MW wind (Prowind)</td><td>Presented; no position yet</td><td>{_src("minto")}</td></tr>
</tbody></table></div>
<p>New requests reach councils every week ahead of <a href="{root}guides/lt2-window-2/">LT2 Window 2</a>. Public decisions appear on the <a href="{root}tracker.html">tracker</a> 14 days after subscribers get them.</p>
{_faq_html(faq)}
{_cta(root)}
{_sources("e1_table", "c1_table", "ottawa_memo", "elt1", "canrea_lt1", "ottawa_engage", "shuniah", "elora", "puslinch", "minto")}"""
    return _page("solar-and-battery-projects-ontario", "Solar farms and battery storage projects in Ontario, by municipality",
                 "Ontario solar farms and battery storage projects with IESO LT2 contracts, by municipality, plus recent council support decisions on new proposals.",
                 "Solar farms and battery storage projects in Ontario",
                 "Which Ontario solar and battery storage projects hold IESO contracts, where they are, and how councils voted on recent proposals.",
                 body, today, crumb="Solar and battery projects", faq=faq)


def where_councils_stand(today: date, slugs: dict, timeline) -> str:
    root = "../../"

    def m(name):
        return _muni(name, name, slugs, root)
    faq = [("How many Ontario councils have rejected wind projects?",
            "The Atmospheric Fund reported in December 2025, citing Wind Concerns Ontario, that at least 159 councils had passed blanket resolutions rejecting all wind projects."),
           ("Which Ontario municipalities support solar projects?",
            "As of December 2025, Mississauga, Whitby, Pickering, Richmond Hill and Caledon had passed resolutions supporting new solar projects, and Toronto had adopted a blanket resolution supporting clean energy proposals."),
           ("Do Ontario councils support natural gas plants?",
            "More than 20 municipal support resolutions for new natural gas projects had passed under LT2 by December 2025, including in Leamington and St. Clair Township.")]
    body = f"""
<p>Each Ontario council decides which energy projects can bid in IESO procurements, and their positions differ sharply by technology. Wind faces the most blanket refusals; solar, storage and gas have more paths to support. {_src("taf")} Technology guides: <a href="{root}guides/wind-projects-ontario/">wind</a>, <a href="{root}guides/solar-and-battery-projects-ontario/">solar and batteries</a>, <a href="{root}guides/agrivoltaics-ontario/">agrivoltaics</a>, <a href="{root}guides/new-nuclear-ontario/">new nuclear</a>.</p>

<h2>By technology</h2>
<div class="scroll"><table class="tbl"><thead><tr><th>Technology</th><th>What councils have done</th><th>Source</th></tr></thead><tbody>
<tr><td><strong>Wind</strong></td><td>At least 159 councils passed blanket resolutions rejecting all wind projects. Of 20 recent wind proposals, 3 got municipal approval, and 2 of those were later withdrawn.</td><td>{_src("taf")}</td></tr>
<tr><td><strong>Solar</strong></td><td>Mississauga, Whitby, Pickering, Richmond Hill and Caledon passed resolutions supporting new solar; most are rooftop projects of about 1 MW. Toronto adopted blanket support for clean energy proposals.</td><td>{_src("taf")}</td></tr>
<tr><td><strong>Natural gas</strong></td><td>More than 20 support resolutions for new gas projects under LT2, including in Leamington and St. Clair Township.</td><td>{_src("taf")}</td></tr>
<tr><td><strong>Battery storage</strong></td><td>Mixed: Ottawa and Centre Wellington supported projects; Shuniah refused a 400 MW project.</td><td>{_src("ottawa_engage", "elora", "shuniah")}</td></tr>
</tbody></table></div>

<h2>Councils with rules or recent decisions</h2>
<div class="scroll"><table class="tbl"><thead><tr><th>Council</th><th>Position</th><th>Source</th></tr></thead><tbody>
<tr><td>{m("Haldimand County")}</td><td>Blanket support with criteria; staff issue letters. Solar, storage, hydro, biomass, nuclear and gas are eligible; wind isn't.</td><td>{_src("haldimand")}</td></tr>
<tr><td>{m("City of Richmond Hill")}</td><td>Staff proposed delegated blanket support for solar; other technologies go to council.</td><td>{_src("richmondhill")}</td></tr>
<tr><td>{m("Township of Selwyn")}</td><td>Written protocol for support requests (By-law 2025-049).</td><td>{_src("selwyn")}</td></tr>
<tr><td>{m("Township of Puslinch")}</td><td>No support until its IESO protocol is written, expected Q1 2027.</td><td>{_src("puslinch")}</td></tr>
<tr><td>{m("Town of Minto")}</td><td>Prowind presented 70 MW of wind and 24 MW of solar; council hasn't taken a position.</td><td>{_src("minto")}</td></tr>
<tr><td>{m("Township of Wellesley")}</td><td>RES Canada presented an early 200 MW wind proposal; the mayor called opinion roughly split.</td><td>{_src("wellesley")}</td></tr>
<tr><td>{m("City of Ottawa")}</td><td>Stepped LT2 process; supported a battery project in December 2025.</td><td>{_src("ottawa_engage")}</td></tr>
<tr><td>{m("Municipality of Shuniah")}</td><td>Refused support for a 400 MW storage project in December 2025.</td><td>{_src("shuniah")}</td></tr>
</tbody></table></div>
<p>Councils change: the councils elected on October 26, 2026 took office on November 15 and will decide <a href="{root}guides/lt2-window-2/">LT2 Window 2</a> requests. Look up any council: <a href="{root}councils/">all 150 councils we read</a>.</p>
{_faq_html(faq)}
{_cta(root)}
{_sources("taf", "haldimand", "richmondhill", "selwyn", "puslinch", "minto", "wellesley", "ottawa_engage", "elora", "shuniah")}"""
    return _page("where-ontario-councils-stand", "Where Ontario councils stand on solar, wind, batteries and gas",
                 "Which Ontario councils reject wind, support solar, back gas plants or have protocols for IESO energy projects, with sources for every decision.",
                 "Where Ontario councils stand on energy projects",
                 "Which councils reject wind, support solar, back gas or have written rules for IESO projects, with a source for each.",
                 body, today, crumb="Where councils stand", faq=faq)


def new_nuclear(today: date, slugs: dict, timeline) -> str:
    root = "../../"

    def m(name, label=None):
        slug = slugs.get(name)
        return f'<a href="{root}councils/{slug}/">{_e(label or name)}</a>' if slug else _e(label or name)
    faq = [("Where is the Wesleyville nuclear project?",
            "At Ontario Power Generation's Wesleyville site in the Municipality of Port Hope, on Lake Ontario. OPG is studying up to "
            "10,000 MWe of new nuclear there; the federal impact assessment is under way and no reactor technology has been chosen."),
           ("Is the Darlington SMR under construction?",
            "Yes. The Canadian Nuclear Safety Commission lists one BWRX-300 unit under construction at Darlington in Clarington. "
            "The licence to construct was granted in April 2025, and OPG has said the first unit should be in commercial service by 2030."),
           ("How big is the Bruce C project?",
            "Up to 4,800 MWe of new nuclear capacity at the existing Bruce Power site in the Municipality of Kincardine. It is going "
            "through an integrated federal impact assessment by a review panel.")]
    body = f"""
<div class="keyfacts">
<div class="stat"><strong>3</strong><span>new nuclear projects, three host councils</span></div>
<div class="stat"><strong>Up to 10,000 MWe</strong><span>proposed at Wesleyville, Port Hope</span></div>
<div class="stat"><strong>1 unit</strong><span>under construction at Darlington</span></div>
</div>
<p>Ontario is planning new nuclear generation alongside the wind, solar and storage it buys through the IESO. The IESO says the province's electricity demand could grow by as much as 90% by 2050. {_src("ieso_w1_overview")} Three new nuclear projects are moving, each at an existing nuclear site and each with a host council: {m("Municipality of Clarington", "Clarington")}, {m("Municipality of Port Hope", "Port Hope")} and {m("Municipality of Kincardine", "Kincardine")}.</p>

<h2>The three projects</h2>
<div class="scroll"><table class="tbl"><thead><tr><th>Project and host council</th><th>Proponent</th><th>Size</th><th>Where it stands</th></tr></thead><tbody>
<tr><td><strong>Darlington New Nuclear Project</strong><span class="m">{m("Municipality of Clarington")}</span></td><td>Ontario Power Generation</td><td>Up to 4 BWRX-300 small modular reactors, 300 MWe each</td><td>Licence to construct one unit granted April 2025 (valid to March 31, 2035). One unit under construction. OPG applied for a 20-year operating licence on March 25, 2026. {_src("cnsc_dnnp")}</td></tr>
<tr><td><strong>New Nuclear at Wesleyville</strong><span class="m">{m("Municipality of Port Hope")}</span></td><td>Ontario Power Generation</td><td>Up to 10,000 MWe; technology not yet selected</td><td>Federal impact assessment started with OPG's Initial Project Description (public notice January 12, 2026). {_src("iaac_wes_notice", "iaac_wes")}</td></tr>
<tr><td><strong>Bruce C Nuclear Project</strong><span class="m">{m("Municipality of Kincardine")}</span></td><td>Bruce Power</td><td>Up to 4,800 MWe; reactor-neutral assessment</td><td>Integrated impact assessment by a review panel, now in Phase 2 (impact statement). {_src("cnsc_bruce", "iaac_bruce")}</td></tr>
</tbody></table></div>

<h2>Darlington SMRs (Clarington)</h2>
<p>OPG chose the GE Vernova Hitachi BWRX-300 for the Darlington site in December 2021 and applied for a licence to construct in October 2022. The Commission authorized construction of one reactor in April 2025, and the first regulatory hold point (the reactor building foundation) was lifted on March 30, 2026. A future application could cover up to three more units. {_src("cnsc_dnnp")} The province approved construction of the first of four units on May 8, 2025. OPG expects that unit in service by the end of 2030, producing 300 MW, enough for about 300,000 homes; the full fleet of four would produce 1,200 MW. {_src("opg_smr", "opg_newnuclear")} The four units are budgeted at $20.9 billion. {_src("cbc_smr")}</p>

<h2>Wesleyville (Port Hope)</h2>
<p>OPG is studying up to 10,000 MWe at its Wesleyville site, assessed for a 78-year operating life with on-site storage of used fuel. The federal assessment uses a bounding approach because no technology has been chosen. {_src("iaac_wes")} OPG and the Municipality of Port Hope signed a memorandum of understanding on February 12, 2026, and OPG's own timeline puts regulatory approvals and agreements with Port Hope and First Nations in the late 2020s. {_src("opg_wes_letter")} OPG updated Port Hope council on April 21, 2026 and held public sessions in Port Hope and {m("Town of Cobourg", "Cobourg")} that May. {_src("opg_wes_council")} Some residents have pushed back, citing the town's history of radioactive waste cleanup; the mayor has said that cleanup and the Wesleyville project are separate. {_src("bnn_wes")}</p>

<h2>Bruce C (Kincardine)</h2>
<p>Bruce Power proposes up to 4,800 MWe of new capacity at its existing site in Kincardine. {_src("cnsc_bruce")} The Impact Assessment Agency decided on December 20, 2024 that a federal impact assessment is required, and the assessment is being run by a review panel. {_src("iaac_bruce_dec", "iaac_bruce")} Nearby councils we read include {m("Town of Saugeen Shores", "Saugeen Shores")}, {m("Township of Huron-Kinloss", "Huron-Kinloss")} and {m("Bruce County")}.</p>

<h2>What host councils decide</h2>
<p>Nuclear projects are licensed by the Canadian Nuclear Safety Commission, but host councils are involved through agreements with the proponent and the federal impact assessment, as Port Hope's memorandum with OPG shows. {_src("opg_wes_letter")} Council Radar reads the agendas and minutes of these councils every morning and reports new nuclear items alongside solar, wind, storage and gas. See <a href="{root}guides/where-ontario-councils-stand/">where Ontario councils stand on energy projects</a>.</p>
{_faq_html(faq)}
{_cta(root)}
{_sources("cnsc_dnnp", "opg_smr", "opg_newnuclear", "cbc_smr", "iaac_wes", "iaac_wes_notice", "opg_wes_letter", "opg_wes_council", "bnn_wes", "cnsc_bruce", "iaac_bruce", "iaac_bruce_dec", "ieso_w1_overview")}"""
    return _page("new-nuclear-ontario", "New nuclear in Ontario: Wesleyville, Darlington SMR and Bruce C",
                 "Ontario's three new nuclear projects: Darlington SMRs in Clarington, Wesleyville in Port Hope and Bruce C in Kincardine. Size, status and host councils, with sources.",
                 "New nuclear projects in Ontario",
                 "Where the Darlington SMRs, Wesleyville and Bruce C stand, how big each is, and which councils host them.",
                 body, today, crumb="New nuclear", faq=faq)


def wind_projects(today: date, slugs: dict, timeline) -> str:
    root = "../../"

    def m(name, label=None):
        slug = slugs.get(name)
        return f'<a href="{root}councils/{slug}/">{_e(label or name)}</a>' if slug else _e(label or name)
    wind = [r for r in ENERGY_W1 if r[4] == "Wind"]
    w_rows = "".join(f"<tr><td>{_muni(r[0], r[1], slugs, root)}</td><td>{_e(r[2])}<br><span class='m'>{_e(r[3])}</span></td>"
                     f"<td class='n'>{r[5]:,.0f}</td><td class='n'>${r[7]:,.2f}</td></tr>" for r in wind)
    faq = [("How many wind farms won IESO LT2 contracts?",
            "The IESO selected two wind projects (400 MW) in LT2 Window 1. One signed its contract: Northern Breeze, 200 MW, "
            "in the Unorganized District of Thunder Bay."),
           ("Can existing Ontario wind farms bid for new contracts?",
            "Yes. LT2 Window 2 allows repowering of existing facilities over 1 MW that meet the IESO's eligibility paths, for new "
            "20-year contracts. Repowering proposals still need municipal support."),
           ("Do Ontario councils support wind turbines?",
            "Mostly not. The Atmospheric Fund reported in December 2025 that at least 159 councils had passed blanket resolutions "
            "rejecting all wind projects, and only 3 of 20 recent wind proposals got municipal approval.")]
    body = f"""
<div class="keyfacts">
<div class="stat"><strong>1</strong><span>new wind contract signed in LT2 Window 1</span></div>
<div class="stat"><strong>159+</strong><span>councils with blanket wind refusals</span></div>
<div class="stat"><strong>Repowering</strong><span>allowed in Window 2</span></div>
</div>
<p>New wind in Ontario comes through the IESO's procurements, and every wind project on municipal land needs that council's support before it can bid. That is the hardest step for wind: more councils have refused wind outright than any other technology. {_src("taf", "ottawa_memo")}</p>

<h2>Wind in LT2 Window 1</h2>
<p>The IESO selected 2 wind projects, 400 MW in total, alongside 12 solar projects. {_src("ieso_w1_overview")} Twelve solar contracts and one wind contract were signed. {_src("ieso_llt_jun")} The wind contract is in the north, on Crown land:</p>
<div class="scroll"><table class="tbl"><thead><tr><th>Location</th><th>Project and proponent</th><th class="n">MW</th><th class="n">$/MWh</th></tr></thead><tbody>{w_rows}</tbody></table></div>
<p>Source for prices and locations: the IESO's final result table. {_src("e1_table")} Every project: <a href="{root}guides/lt2-window-1-results/">LT2 Window 1 results by municipality</a>.</p>

<h2>Other recent wind contracts</h2>
<p>The IESO's medium-term procurements have also contracted wind: MT1 included 1 wind facility, and MT2(e) contracted 995 MW, including 16 wind facilities, on 5-year contracts starting between 2026 and 2029. {_src("ieso_apr21")}</p>

<h2>Window 2: repowering existing wind farms</h2>
<p>For the first time, LT2 Window 2 lets existing facilities over 1 MW rebuild or upgrade and compete for a new 20-year contract, if they meet one of the IESO's eligibility paths. The mandatory municipal support requirement applies to repowering too. {_src("w2_pres")} Dates and rules: <a href="{root}guides/lt2-window-2/">LT2 Window 2 guide</a>.</p>

<h2>Where councils stand on wind</h2>
<div class="scroll"><table class="tbl"><thead><tr><th>Council</th><th>Position or proposal</th><th>Source</th></tr></thead><tbody>
<tr><td>Across Ontario</td><td>At least 159 councils have blanket resolutions rejecting all wind projects. Of 20 recent wind proposals, 3 got municipal approval, and 2 of those were later withdrawn.</td><td>{_src("taf")}</td></tr>
<tr><td>{m("Haldimand County")}</td><td>Blanket support for energy projects that meet its criteria, but wind isn't eligible.</td><td>{_src("haldimand")}</td></tr>
<tr><td>{m("Town of Minto")}</td><td>Prowind presented 70 MW of wind and 24 MW of solar; residents raised concerns and council hasn't taken a position.</td><td>{_src("minto")}</td></tr>
<tr><td>{m("Township of Wellesley")}</td><td>RES Canada presented an early-stage 200 MW wind proposal; the mayor described opinion as roughly split.</td><td>{_src("wellesley")}</td></tr>
</tbody></table></div>
<p>New councils elected on October 26, 2026 will hear Window 2 requests, and some may revisit earlier refusals. More: <a href="{root}guides/where-ontario-councils-stand/">where Ontario councils stand</a> and <a href="{root}guides/council-decisions/">council decisions by month</a>.</p>
{_faq_html(faq)}
{_cta(root)}
{_sources("ieso_w1_overview", "ieso_llt_jun", "e1_table", "ieso_apr21", "w2_pres", "taf", "ottawa_memo", "haldimand", "minto", "wellesley")}"""
    return _page("wind-projects-ontario", "Wind farms in Ontario: IESO contracts and council positions",
                 "Ontario wind farms with IESO contracts, repowering in LT2 Window 2, and where councils stand on wind turbines, from IESO tables and council records.",
                 "Wind farms and wind turbines in Ontario",
                 "Which new wind projects hold IESO contracts, how repowering works in Window 2, and why council support is the hardest step for wind.",
                 body, today, crumb="Wind projects", faq=faq)


def agrivoltaics(today: date, slugs: dict, timeline) -> str:
    root = "../../"
    agv = [r for r in ENERGY_W1 if "Agrivoltaics" in r[2]]
    a_rows = "".join(f"<tr><td>{_muni(r[0], r[1], slugs, root)}</td><td>{_e(r[2])}<br><span class='m'>{_e(r[3])}</span></td>"
                     f"<td class='n'>{r[5]:,.2f}</td><td class='n'>${r[7]:,.2f}</td></tr>" for r in agv)
    total = sum(r[5] for r in agv)
    faq = [("What is agrivoltaics?",
            "A dual land use where solar panels and farming share the same land, designed so the land stays in agricultural production."),
           ("Did agrivoltaic projects win IESO contracts in Ontario?",
            f"Yes. {len(agv)} projects named as agrivoltaics signed LT2 Window 1 contracts, {total:,.1f} MW in total, in "
            + ", ".join(r[0] for r in agv) + "."),
           ("Can solar be built on prime farmland under LT2?",
            "No new ground-mounted solar is permitted in prime agricultural areas, and no new electricity projects in specialty crop areas. "
            "Other projects in prime agricultural areas need an Agricultural Impact Assessment completed to the local municipality's satisfaction.")]
    body = f"""
<div class="keyfacts">
<div class="stat"><strong>{len(agv)}</strong><span>agrivoltaic projects with LT2 contracts</span></div>
<div class="stat"><strong>{total:,.1f} MW</strong><span>combined capacity</span></div>
<div class="stat"><strong>Council</strong><span>decides on Agricultural Impact Assessments</span></div>
</div>
<p>Agrivoltaics combines solar panels and farming on the same land, designed to keep it in agricultural production. {_src("agv_canada")} In Ontario's LT2 procurement, the southern solar projects that won were small, and three of them are agrivoltaic. {_src("e1_table")}</p>

<h2>Agrivoltaic projects with LT2 contracts</h2>
<div class="scroll"><table class="tbl"><thead><tr><th>Municipality</th><th>Project and proponent</th><th class="n">MW</th><th class="n">$/MWh</th></tr></thead><tbody>{a_rows}</tbody></table></div>
<p>All signed 20-year contracts in the LT2 energy stream. {_src("e1_table")} Every project: <a href="{root}guides/lt2-window-1-results/">LT2 Window 1 results by municipality</a>.</p>

<h2>The farmland rules in LT2</h2>
<ul>
<li><strong>Specialty crop areas are off limits</strong> to new electricity projects, and <strong>new ground-mounted solar isn't permitted in prime agricultural areas.</strong> {_src("omafa_23")}</li>
<li><strong>The council decides on the Agricultural Impact Assessment.</strong> Projects proposed in prime agricultural areas need an AIA completed to the satisfaction of the local municipality; the agriculture ministry advises but doesn't approve. {_src("ieso_aia_qa")}</li>
<li><strong>Two stages.</strong> The first (avoid) is done before the bid; the second and third (minimize and mitigate) must be met within 18 months of the contract award. {_src("amo_lt2req")}</li>
</ul>
<p>Agrivoltaics Canada argued in December 2024 that the IESO's framework treats agrivoltaics the same as ground-mounted solar, without recognizing its farming benefits, and asked the province to change that. {_src("agv_canada")} The IESO is also reviewing how the AIA applies to repowered sites in Window 2. {_src("w2_pres")}</p>

<h2>Why it matters for Window 2</h2>
<p>For solar on farmland in southern Ontario, the site's designation and the council's view of the AIA decide whether a project can bid. Councils set their own protocols for support requests, and new councils took office on November 15, 2026. See <a href="{root}guides/municipal-support-resolution/">how municipal support resolutions work</a> and <a href="{root}guides/solar-and-battery-projects-ontario/">solar and battery projects in Ontario</a>.</p>
{_faq_html(faq)}
{_cta(root)}
{_sources("agv_canada", "e1_table", "omafa_23", "ieso_aia_qa", "amo_lt2req", "w2_pres")}"""
    return _page("agrivoltaics-ontario", "Agrivoltaics in Ontario: LT2 projects and farmland rules",
                 "Ontario agrivoltaic solar projects with IESO LT2 contracts, plus the prime agricultural area and Agricultural Impact Assessment rules councils apply.",
                 "Agrivoltaics in Ontario",
                 "The agrivoltaic projects that won LT2 contracts, the farmland rules that apply, and the council's role in the Agricultural Impact Assessment.",
                 body, today, crumb="Agrivoltaics", faq=faq)


def integrated_energy_plan(today: date, slugs: dict, timeline) -> str:
    root = "../../"
    faq = [("What is Ontario's Integrated Energy Plan?",
            "Energy for Generations is Ontario's first integrated energy plan, released on June 12, 2025. It covers electricity, natural gas, "
            "hydrogen, storage and other energy sources together, with a planning horizon to 2050, and is to be renewed on a five-year cycle."),
           ("Who is Ontario's energy minister?",
            "Stephen Lecce is Ontario's Minister of Energy and Mines. He released the Integrated Energy Plan in June 2025 and presented the "
            "ministry's 2026–27 estimates to the legislature's Standing Committee on the Interior on September 29, 2026."),
           ("How much will Ontario's electricity demand grow?",
            "Law firm summaries of the plan put growth at about 75% over the next 25 years. The IESO says demand could grow by as much as 90% by 2050."),
           ("What does the Integrated Energy Plan mean for municipalities?",
            "The province buys most new supply through IESO procurements like LT2, and in those, municipalities decide whether they are "
            "willing hosts. A project on municipal land needs a council support resolution before it can bid.")]
    body = f"""
<div class="keyfacts">
<div class="stat"><strong>June 12, 2025</strong><span>Ontario's first integrated energy plan released</span></div>
<div class="stat"><strong>2050</strong><span>planning horizon</span></div>
<div class="stat"><strong>5 years</strong><span>planning cycle from 2025</span></div>
</div>
<p><em>Energy for Generations: Ontario's Integrated Plan to Power the Strongest Economy in the G7</em> is Ontario's first integrated energy plan. It sets a planning horizon to 2050 and brings electricity, natural gas, hydrogen, storage and other energy sources into one plan. {_src("iep_page")} It was approved by Order in Council on June 11, 2025 under the Electricity Act, 1998, which lets the minister issue such a plan with cabinet approval. {_src("iep_oic")} Minister of Energy and Mines Stephen Lecce launched it on June 12, 2025. {_src("blakes_iep")}</p>

<h2>What the plan says</h2>
<ul>
<li><strong>Demand is rising fast.</strong> Summaries of the plan put electricity demand growth at about 75% over the next 25 years. {_src("blakes_iep")} The IESO's own outlook says up to 90% by 2050. {_src("ieso_w1_overview")}</li>
<li><strong>Nuclear and hydro stay the backbone.</strong> Together they supply nearly 75% of Ontario's electricity today. {_src("torys_iep")} The plan backs new nuclear at Bruce Power and Port Hope and four SMRs at Darlington totalling 1,200 MW. {_src("iep_page", "mccarthy_iep")} See <a href="{root}guides/new-nuclear-ontario/">new nuclear projects in Ontario</a>.</li>
<li><strong>Natural gas keeps a role.</strong> The plan includes Ontario's first Natural Gas Policy Statement, which treats gas as a key part of the energy mix for growth, reliability and affordability. {_src("torys_iep", "ngps_ero")}</li>
<li><strong>Planning repeats every five years.</strong> Starting in 2025, Ontario runs a five-year cycle of integrated planning across all fuels. {_src("mccarthy_iep")}</li>
<li><strong>The IESO and OEB carry it out.</strong> Ministerial directives tell the IESO and the Ontario Energy Board to implement the plan, including in the IESO's Annual Planning Outlook and regional plans. {_src("iep_ieso_dir", "mccarthy_iep")}</li>
</ul>

<h2>Who decides: the minister, the IESO and councils</h2>
<p>Stephen Lecce is Minister of Energy and Mines; he presented the ministry's 2026–27 estimates to the legislature's Standing Committee on the Interior on September 29, 2026. {_src("ola_estimates")} On September 10, 2026, Matthew Rae was designated Associate Minister of Energy-Intensive Industries in the same ministry. {_src("oic_rae")} The minister directs the IESO, which plans the grid and runs procurements like LT2. {_src("ieso_corp")} In those procurements, municipalities determine whether they are willing hosts for new supply. {_src("ieso_municipal")} The province is also reviewing its Municipal Energy Plan grant program to support community energy planning. {_src("mep_ero")}</p>

<h2>What it means for the next council term</h2>
<p>The plan's new supply still has to be sited somewhere, and for solar, wind, storage and gas on municipal land, that means a council vote. Councils elected on October 26, 2026 will hear the support requests for <a href="{root}guides/lt2-window-2/">LT2 Window 2</a>, with proposals expected in 2027. See <a href="{root}guides/municipal-support-resolution/">how municipal support resolutions work</a> and <a href="{root}guides/where-ontario-councils-stand/">where Ontario councils stand</a>.</p>
{_faq_html(faq)}
{_cta(root)}
{_sources("iep_page", "iep_oic", "blakes_iep", "torys_iep", "mccarthy_iep", "ngps_ero", "iep_ieso_dir", "iep_ieso_news", "ieso_w1_overview", "ola_estimates", "oic_rae", "ieso_corp", "ieso_municipal", "mep_ero")}"""
    return _page("ontario-integrated-energy-plan", "Ontario Integrated Energy Plan (Energy for Generations) explained",
                 "What Ontario's Integrated Energy Plan says about demand, nuclear, gas and procurement, who the energy minister is, and what it means for councils.",
                 "Ontario's Integrated Energy Plan, explained",
                 "What <em>Energy for Generations</em> commits to, who carries it out, and why council votes still decide where new supply goes.",
                 body, today, crumb="Integrated Energy Plan", faq=faq)


CATEGORY_LABELS = {"support_granted": "Support granted", "support_denied": "Support refused or not yet given",
                   "policy_protocol": "New protocol or criteria"}


def council_decisions(today: date, slugs: dict, items: list[dict]) -> str:
    """Every public council decision, newest month first. Rebuilt on every deploy from the tracker's public items,
    so it gains a new month section as decisions are published (14 days after subscribers get them)."""
    root = "../../"
    rows = sorted((i for i in items if i.get("meeting_date")), key=lambda i: i["meeting_date"], reverse=True)
    months: dict[str, list[dict]] = {}
    for i in rows:
        months.setdefault(i["meeting_date"][:7], []).append(i)
    sections = []
    for ym, its in months.items():
        label = date(int(ym[:4]), int(ym[5:7]), 1).strftime("%B %Y")
        lis = "".join(
            f'<li><strong>{_muni(i.get("municipality", ""), i.get("municipality"), slugs, root)}</strong>: {_e(i.get("headline"))}'
            f'<br><span class="m">{_e(CATEGORY_LABELS.get(i.get("category"), ""))}'
            f'{" · " + _e(i["technology"]) if i.get("technology") else ""}'
            f'{" · " + _e(str(i["capacity_mw"])) + " MW" if i.get("capacity_mw") else ""}'
            f'{" · " + _e(date.fromisoformat(i["meeting_date"][:10]).strftime("%B %-d")) if len(i["meeting_date"]) >= 10 else ""}'
            f'{" · " + chr(60) + "a href=" + chr(34) + _e(i["source_url"]) + chr(34) + " rel=" + chr(34) + "nofollow" + chr(34) + ">Source</a>" if i.get("source_url") else ""}</span></li>'
            for i in its)
        sections.append(f'<h2>{label} <span class="m">({len(its)})</span></h2><ul class="declist">{lis}</ul>')
    n_c = len({i.get("municipality") for i in rows})
    body = (f'<p>{len(rows)} public decisions from {n_c} councils so far, newest first. Subscribers get each one in the Monday '
            f'email; it appears here 14 days later. For every item with its full summary, see the '
            f'<a href="{root}tracker.html">municipal support tracker</a>.</p>'
            + "".join(sections) +
            f'<p>Related: <a href="{root}guides/where-ontario-councils-stand/">Where Ontario councils stand</a> · '
            f'<a href="{root}guides/lt2-window-2/">LT2 Window 2 guide</a></p>{_cta(root)}')
    html_ = _page("council-decisions", "Ontario council energy decisions, by month",
                  "Every public Ontario council decision on solar, wind, battery storage and gas projects, grouped by month, "
                  "with a source link for each. Updated as decisions are published.",
                  "Ontario council energy decisions, by month",
                  "Support given, support refused and new rules on energy projects, month by month, from 150 Ontario councils.",
                  body, today, crumb="Council decisions by month")
    return html_.replace("</style>", ".declist{list-style:none;padding:0}.declist li{padding:.7rem 0;border-bottom:1px solid var(--line)}"
                         ".declist .m{display:block;color:var(--muted);font-size:.88rem;margin-top:.2rem}</style>", 1)


PAGES = [
    ("lt2-window-2", lt2_window_2, "IESO LT2 Window 2: dates, rules and municipal support",
     "When proposals are due, what's new compared with Window 1, and why council support decides which projects can bid."),
    ("lt2-window-1-results", lt2_window_1_results, "LT2 Window 1 results by municipality",
     "Every energy and capacity contract, where it is, its size and its price."),
    ("municipal-support-resolution", municipal_support, "Municipal support resolutions for IESO projects",
     "MRSPS versus blanket resolutions, how the process runs, and how councils handle it."),
    ("solar-and-battery-projects-ontario", solar_battery, "Solar farms and battery storage projects in Ontario",
     "Contracted projects by municipality, and recent council decisions on new proposals."),
    ("where-ontario-councils-stand", where_councils_stand, "Where Ontario councils stand on energy projects",
     "Wind refusals, solar and gas support, and councils with written rules."),
    ("wind-projects-ontario", wind_projects, "Wind farms and wind turbines in Ontario",
     "New wind contracts, repowering in Window 2, and where councils stand on wind."),
    ("agrivoltaics-ontario", agrivoltaics, "Agrivoltaics in Ontario",
     "Agrivoltaic projects with LT2 contracts and the farmland rules councils apply."),
    ("new-nuclear-ontario", new_nuclear, "New nuclear projects in Ontario",
     "Darlington SMRs, Wesleyville and Bruce C: size, status and host councils."),
    ("ontario-integrated-energy-plan", integrated_energy_plan, "Ontario's Integrated Energy Plan, explained",
     "What Energy for Generations commits to, and who carries it out."),
    ("council-decisions", None, "Ontario council energy decisions, by month",
     "Every public council decision, month by month, with a source for each."),
]


def index_page(today: date) -> str:
    root = "../"
    items = "".join(f'<li><a href="{slug}/">{_e(t)}</a><p>{_e(d)}</p></li>' for slug, _, t, d in PAGES)
    main = (f'<main class="prose"><p class="crumbs"><a href="{root}index.html">Home</a> › Guides</p>'
            f'<h1>Guides to Ontario energy procurement and council support</h1>'
            f'<p class="lede">Plain-language guides for developers, consultants and lawyers working on IESO projects in Ontario, '
            f'built from IESO documents and council records.</p>'
            f'<p>Every project in the IESO\'s Long-Term 2 (LT2) procurement that sits on municipal land needs a support '
            f'resolution from that council before it can bid. These guides cover the Window 2 timeline and rules, who won '
            f'Window 1 and where, how municipal support resolutions work, where each Ontario council stands on solar, '
            f'wind, battery storage and gas, and the new nuclear projects at Darlington, Wesleyville and Bruce. Each fact links to the IESO document or council record it comes from, and the '
            f'pages are rebuilt every day from the same records Council Radar reads for its Monday email.</p>'
            f'<ul class="guides">{items}</ul>{_cta(root)}</main>')
    html_ = _shell("Guides: IESO LT2 and Ontario council support | Council Radar",
                   "Guides to IESO LT2 Window 2, Window 1 results, municipal support resolutions and where Ontario councils stand on energy projects.",
                   SITE_URL + "guides/", root, main, image=SITE_URL + "og/home.png")
    return html_.replace("</style>", GUIDE_CSS + "</style>", 1)


def write(today: date, council_slugs: dict[str, str], out_dir: Path | None = None, items: list[dict] | None = None) -> list[str]:
    """Write the guides and their index. council_slugs maps council name -> page slug (only councils with a page).
    Returns site-relative paths for the sitemap."""
    out_dir = out_dir or (config.ROOT / "site" / "guides")
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    tl_path = config.ROOT / "data" / "lt2_timeline.json"
    timeline = json.loads(tl_path.read_text()) if tl_path.exists() else None
    paths = ["guides/"]
    (out_dir / "index.html").write_text(index_page(today))
    for slug, fn, _, _ in PAGES:
        p = out_dir / slug / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(council_decisions(today, council_slugs, items or []) if fn is None else fn(today, council_slugs, timeline))
        paths.append(f"guides/{slug}/")
    return paths
