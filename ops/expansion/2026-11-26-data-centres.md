# Expansion memo: Data centres and large loads, Ontario

Date: 2026-11-26 · Candidate 1 · Verdict: **GO, as a collect-only beta.** The feed is `datacentres` in `feeds.yaml` (`enabled: false`, `collect: true`). Launch: Dec 10 at earliest.

## Why now
- Ontario says data-centre connection requests "could total more than 10,000 MW". Peak demand is about 25,000 MW [1].
- The draft Playbook (ERO 026-0853) adds provincial connection approval and a higher rate class [1][2]; municipalities keep land-use planning [3].
- Councils are acting:
  - Oakville (Aug 11) and Mississauga (Sept 16, 10 MW+) passed one-year interim control by-laws (ICBLs) [4][5].
  - Hamilton, Milton and Burlington voted pauses down [5].
  - Toronto, Ottawa and Waterloo Region ordered studies [5].
  - Sault Ste. Marie is drafting rules; Greater Napanee permits them on industrial land [5]. Chatham-Kent reports in December [4].
- Our excerpts, saved only for other feeds, already hold 3 items: Hamilton Planning Committee (Dec 1: AI data centres study, ERO response), North Grenville (Nov 3: proposed one-year ICBL) and Orangeville (Nov 23: Mulmur and Melancthon letters).

## Who buys, how many
- **Operators and developers:** 74 providers run 142 Ontario facilities [6]. ENCOR counts 36 providers and 69 facilities [7].
- **Projects:** Hive Digital, 320 MW in the GTA [5]. Microsoft, 3 sites totalling ~200 MW [8].
- **Landlords:** Prologis markets "data-centre-ready" parks in Mississauga and Brampton [4].
- **Law firms:** 6 have published data-centre notes since July: McCarthy, Torys, Gowling, Miller Thomson, BLG and Dentons [2][9]–[13].
- **Power developers:** the Playbook encourages "bring your own generation" [2]; our energy prospects overlap.

~100 organizations, large budgets.

## What they pay today
- DC Hub: $49–$299/month, enterprise from $699. No permitting data [14].
- TeleGeography: enterprise licence, price on quote [15].
- ontariodatacentres.ca: a free volunteer tracker, "last updated September 2026", with no alerts [4].
- No one sells sourced council alerts.

## Councils and platforms
- 15 councils have data-centre items: the 13 above, Kincardine [16] and Centre Wellington [8].
- 10 of them are on eScribe and read daily: Hamilton, Oakville, Mississauga, Milton, Ottawa, Waterloo Region, Chatham-Kent, Kincardine, North Grenville and Orangeville. Facility hosts Vaughan, Markham, Cambridge, Brampton, Thorold and Guelph are too.
- Not read:
  - Toronto (TMMIS; robots.txt unchecked).
  - Greater Napanee and Centre Wellington (CiviCweb, disallowed).
  - Sault Ste. Marie and Burlington (not listed).

## Cost
The 7 patterns hit 25 times at 3 councils in 10 days of excerpts. Assumption: 10–30 AI reads a week at ~$0.02, under $3/month, plus 1 hour of editing a week.

## Revenue (MRR)
| Case | Mix | MRR | Assumption |
|---|---|---|---|
| Low | 10 × $59 + 3 × $249 | $1,337 | 13 buyers, ~13% of the pool |
| Base | 20 × $59 + 10 × $249 + 2 × $990 | $5,650 | ~30% of the pool, 2 pilots |
| High | 40 × $79 + 25 × $249 + 6 × $990 | $15,325 | Pool widened by energy cross-sells and Toronto |

Launch on the existing links tagged `?client_reference_id=datacentres`; lead with the $990 pilot.

## Risks
- Small pool: sell teams and pilots.
- Noise from IT-budget "data centre" items; the AI drops them.
- Volume is bursty. Oakville's ICBL ends in Aug 2027 and Mississauga's in Sept 2027; both dates are hooks.
- Gaps: Toronto and the CiviCweb councils.
- Provincial approval or the free tracker adding alerts.

## Next
- Dec 10 run: measure volume, then write `samples/datacentres-sample.md` (5+ items from 4+ councils) and launch per `ops/approvals.md`.
- Outreach: use the Dec 1 Hamilton item now.

## Sources
[1] https://ero.ontario.ca/notice/026-0853 · [2] https://www.mccarthy.ca/en/insights/blogs/canadian-energy-perspectives/ontario-launches-data-centre-playbook-proposed-framework-for-grid-access-electricity-costs-and-project-approval · [3] https://www.amcto.com/network-community/blog/ontarios-data-centre-playbook-what-municipalities-need-know · [4] https://ontariodatacentres.ca/ · [5] https://www.bnnbloomberg.ca/business/artificial-intelligence/2026/09/16/heres-how-some-ontario-municipalities-are-grappling-with-new-ai-data-centres/ · [6] https://baxtel.com/data-center/ontario · [7] https://encoradvisors.com/data-centres-ontario/ · [8] https://thenarwhal.ca/ontario-ai-data-centres-explained/ · [9] https://www.torys.com/our-latest-thinking/publications/2026/08/new-framework-for-data-centre-grid-connections · [10] https://gowlingwlg.com/insights-resources/articles/2026/ontario-draft-data-centre-playbook · [11] https://www.millerthomson.com/en/insights/technology-ip-and-privacy/ontarios-data-centre-playbook-what-it-means-for-grid-access/ · [12] https://www.blg.com/en/insights/2026/07/data-centre-regulation-in-ontario · [13] https://www.dentons.com/en/insights/alerts/2026/august/31/planning-act-tool-used-to-pause-data-centres-in-oakville · [14] https://dchub.cloud/pricing?tool=dc · [15] https://www2.telegeography.com/hubfs/assets/product-tear-sheets/Data-Center-Research-Service.pdf · [16] https://www.kincardine.ca/news/posts/media-release-august-27-2026-municipality-of-kincardine-recommends-stronger-protections-to-the-province-of-ontario-regarding-the-proposed-data-centre-playbook/
