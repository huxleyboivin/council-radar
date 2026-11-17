"""Build the sales sample issue from verified public items (Sept-Oct 2026 and earlier policy items).

Live issues are produced by the pipeline from council documents of the past week; this sample
is hand-assembled from public reporting and council documents so prospects can see the format.
"""
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from radar import digest  # noqa: E402

INTRO = (
    "**Sample issue.** Live issues cover the past week of council documents across every monitored "
    "Ontario municipality and link to the council's own files. This sample pulls together items from "
    "recent months so you can see the format.\n\n"
    "**Why this matters now:** Ontario's new councils took office after the October 26 municipal "
    "election. For LT2 Window 2, the IESO expects the final RFP in Q1 2027 and proposals in Q2/Q3 2027, "
    "and municipal support is still mandatory. Every one of those support confirmations will go through "
    "a council that has just changed."
)

ITEMS = [
    {
        "category": "support_denied", "municipality": "Township of Puslinch",
        "headline": "Council acknowledges a 7 MW solar project but doesn't give support yet",
        "status": "decided", "meeting_name": "Council (delegation)", "meeting_date": "2026-10-07",
        "technology": "Solar", "capacity_mw": 7, "proponent": "Landowner-led proponent",
        "summary": ("Council sent a letter confirming it has been informed of the project, rather than a letter of "
                    "support. It asked staff to develop a protocol for IESO projects, including community "
                    "engagement, in Q1 2027, and is writing to the local MPP about how IESO timelines fit with "
                    "municipal planning. What it means: support letters are unlikely before the protocol is in "
                    "place, so plan around Q1 2027."),
        "source_url": "https://www.wellingtonadvertiser.com/brighter-days-may-be-ahead-for-solar-farm-project/",
    },
    {
        "category": "policy_protocol", "municipality": "Haldimand County",
        "headline": "Revised LT2 criteria let the CAO issue support letters; wind is not eligible",
        "status": "decided", "meeting_name": "Council (Report EDT-02-2026)", "meeting_date": "2026-04-07",
        "summary": ("Council unanimously kept blanket support. The CAO can now issue support letters to projects "
                    "that meet the criteria, so proponents don't have to come to council one by one. Eligible: "
                    "ground-mounted solar, battery storage, hydro, biomass, nuclear, natural gas, biogas and "
                    "co-generation in industrial areas; wind turbines remain excluded. Proponents need a public "
                    "website at least 3 months before submitting to the IESO, consultation finished 2 months "
                    "before, and two public meetings with notice to owners within 500 m. A community benefit "
                    "agreement remains mandatory: $1,133/MW per year in 2026, capped at $300,000 per project."),
        "source_url": "https://haldimandpress.com/haldimand-tightens-rules-for-future-energy-project-approvals/",
    },
    {
        "category": "policy_protocol", "municipality": "City of Richmond Hill",
        "headline": "Staff propose a faster support process for solar; other projects go to council",
        "status": "recommended", "meeting_name": "Committee of the Whole (SRPBS.26.004)",
        "meeting_date": "2026-04-01",
        "summary": ("Staff proposed a formal process for municipal support requests: a blanket support resolution, "
                    "with delegated authority, for solar projects, and individual council resolutions for every "
                    "other energy technology. What it means: solar developers may get a faster staff-level path "
                    "here, while storage and other technologies still need a council vote."),
        "evidence": ("both Blanket Municipal Support Resolution (including delegated authority for solar energy "
                     "projects) and Municipal Resolution in Support (for all other energy projects)"),
        "source_url": "https://pub-richmondhill.escribemeetings.com/filestream.ashx?DocumentId=72776",
    },
    {
        "category": "delegation", "municipality": "Town of Minto",
        "headline": "Prowind presents wind and solar proposals; council hasn't taken a position",
        "status": "presented", "meeting_name": "Council delegation / community meetings",
        "meeting_date": "2026-10-08", "technology": "Wind + solar", "proponent": "Prowind",
        "summary": ("Prowind presented a 70 MW, 10-turbine wind project and a 24 MW solar project to council in June, "
                    "and plans to ask for a support resolution for the IESO process. In October, residents held "
                    "information sessions to discuss their concerns. Council has not taken a position. Coming up: "
                    "a support request to the new council is likely, and community interest is high."),
        "source_url": "https://www.wellingtonadvertiser.com/minto-residents-hear-concerns-about-proposed-wind-turbines/",
    },
    {
        "category": "delegation", "municipality": "Township of Wellesley",
        "headline": "RES Canada presents an early-stage 200 MW wind proposal",
        "status": "presented", "meeting_name": "Council delegation", "meeting_date": "June 2026",
        "technology": "Wind", "capacity_mw": 200, "proponent": "RES Canada",
        "summary": ("RES Canada presented an early-stage proposal of up to 30 turbines to township council. The "
                    "mayor described public opinion as roughly evenly split, and land leasing has not started. "
                    "Coming up: a formal support request to the new council is likely ahead of LT2 Window 2."),
        "source_url": "https://www.observerxtra.com/mixed-reviews-for-a-wellesley-wind-turbine-proposal-still-in-its-early-stages/",
    },
]

if __name__ == "__main__":
    subject, body = digest.render(ITEMS, "Council Radar: Ontario Energy Projects", date(2026, 11, 16), INTRO,
                                  period_label="in this sample")
    out = Path(__file__).resolve().parent / "sample-issue.md"
    out.write_text(body)
    print(subject)
    print(out)
