# Expansion memo: Enterprise tier for energy law firms and large developers

Date: 2026-11-23 · Candidate 1 of 7 · Verdict: **GO (conditional)**: pilot by hand with 1–3 design partners first.

## Who buys
- **Energy law firms.** Chambers Canada ranks 44 lawyers at 15 firms in Energy: Power, Regulatory and Transactional [1][2].
- **Large developers and IPPs.** LT2 Window 1 contracted 14 energy proponents (1,315 MW) and 3 storage projects (640 MW) [3][4]. Losing bidders are not published. CanREA has 330+ members nationally [5].
- Target list (assumption): 15 firms plus ~45 developers, consultancies and Indigenous development corporations, so **~60 organizations**.

## What they pay today, and to whom
| Product | Price | Source |
|---|---|---|
| FiscalNote (covers 12,000+ US municipalities) | average $39,255/yr (SMB), $84,180/yr (enterprise) | [6][7] |
| FiscalNote PolicyNote API | $0, $300/month, or custom | [7] |
| Enverus | est. $10–50k per seat/yr; $100k+ enterprise (competitor estimate) | [8] |
| Paces, Heatmap Pro, Transect (US siting data) | not published; Paces has about 100 customers | [9][10][11] |
| Open Council Network (UK council API) | £249 or £549 per month; enterprise on application | [12] |

None of them covers Ontario councils item by item; firms do that by hand.

## Features that justify $750–1,500/month ($9–18k/yr, under FiscalNote's SMB average [6])
1. **All 442 councils.** We read 150 today (`data/health.json`). 119 are on CiviCweb, which robots.txt blocks (`data/platform_survey.yaml`), and the rest use other platforms, so a person covers the gap.
2. **Client watchlists** (municipalities, projects, proponents).
3. **Alerts within 24 hours**, sent from the existing `daily.yml` run.
4. **Historical CSV export** from `radar.db`.
5. **A named analyst** and a monthly memo per matter.
6. Unlimited seats and invoicing, since law firms don't pay by card.

## Keywords, councils, platforms
No new patterns: the tier reuses the `energy` feed, with client watch terms added later. eScribe allows reading and is already covered. CiviCweb disallows crawling, so those councils are concierge only (`ops/civicweb_permission_request.md`).

## Cost to run
Model cost is negligible: the last run read 218 documents with 0 AI calls (`data/health.json`). The real cost is analyst time. Assuming 4–6 hours per account per month at $60/hour (assumption), that is $240–360/month, a 64–76% margin at $990.

## Revenue estimate (MRR)
| Case | Accounts | Price | MRR | Assumption |
|---|---|---|---|---|
| Low | 3 | $750 | $2,250 | 5% of the ~60 targets |
| Base | 10 | $990 | $9,900 | 17%, mostly law firms and the top developers, by LT2 Window 2 |
| High | 25 | $1,250 | $31,250 | Housing feed and a second province bundled in |

The base case alone meets the July 2027 $10k/month milestone (`ops/plan.md`).

## Risks
- **No proof yet.** We have 0 subscribers and 1 reply from 22 week-1 cold emails (`ops/plan.md`), and enterprise buyers want references.
- **The CiviCweb gap** could make analyst hours balloon.
- **Demand follows IESO windows**; expect downgrades between them.
- **Procurement**: NDAs and security questionnaires are legal commitments, so they go to Huxley.
- **US vendors** (Paces, Heatmap) could enter Canada.

## Recommendation
**Go, as a manual pilot.** Offer 1–3 firms (Blakes is already warm) a 60-day pilot of watchlists, 24-hour alerts, export and an analyst, at a proposed $990/month, invoiced. Automate the watchlist overlay, export and daily alert only after one pilot converts. No code changes. Pricing and invoicing are Huxley's call (`ops/browser_queue.md`).

## Sources
[1] https://chambers.com/legal-rankings/energy-power-regulatory-canada-2:1259:50:1 · [2] https://chambers.com/legal-rankings/energy-power-transactional-canada-2:1258:50:1 · [3] https://www.ieso.ca/-/media/Files/IESO/Document-Library/long-term-rfp/LT2-W1-results-overview.pdf · [4] https://ieso.ca/-/media/Files/IESO/Document-Library/long-term-rfp/capacity/LT2c-1-20260611-Public-Result-Table.pdf · [5] https://renewablesassociation.ca/five-years-already/ · [6] https://www.spendhound.com/marketplace/fiscalnote-pricing · [7] https://fiscalnote.com/policynote-api-pricing · [8] https://www.oilpriceapi.com/compare/enverus-pricing · [9] https://latitudemedia.com/news/can-ai-fueled-data-research-save-clean-energy-developers-precious-time · [10] https://netzerocompare.com/software/heatmap-pro · [11] https://netzerocompare.com/software/transect · [12] https://opencouncil.network/api/pricing
