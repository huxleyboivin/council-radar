# Council Radar growth plan (logistics agent)

Written 2026-11-21. Owner: Huxley Boivin. Kept up to date by the "chief of staff" scheduled task, which commits it to `ops/plan.md` in the repo.

## Goals
- **Short term: first paying subscriber by Dec 18, 2026.**
- **Long term: $100,000 a month in recurring revenue.**

## Where things stand (Nov 21)
- Product: 150 of 442 Ontario councils read every day, no errors. One issue sent so far, with 3 items. Site is on getcouncilradar.ca with 159+ indexable pages, 8 guides, GA4 and Search Console coming.
- Sales: 22 cold emails in week 1, 1 polite reply (Blakes, offered 2 free issues on Nov 20), 0 trials, 0 subscribers, $0.
- Prices: $59/month founding (regular $99), $249/month team.

## The bottleneck
It's a distribution problem, not a product problem:
1. **Outreach goes to the wrong inboxes.** 15 of 22 emails went to info@ or role addresses. People buy a $249/month brief, inboxes don't. The developers with named project leads (Boralex, Kruger, Atura, Hydrostor) are on CiviCweb councils we can't read.
2. **No founder-led selling yet.** Every first B2B sale in a niche like this comes from a person talking to a person: a LinkedIn note, a 15-minute call, a free month with personal service.
3. **Thin sample.** One issue with 3 items is hard to sell. Weekly issues and coverage growth fix this over time.

## The math for $100k/month
At today's prices, $100k needs about 400 team plans or 1,700 founding seats. The Ontario energy niche alone (developers, energy law firms, consultants, Indigenous development corporations, utilities, investors) is maybe 200–400 organizations. Realistically that feed tops out around $20–40k/month. Getting to $100k takes four levers stacked together, in this order:
1. **Win the Ontario energy niche** before LT2 Window 2 proposals (expected mid-2027). Target: $5–10k/month.
2. **Add a higher tier.** For example $750–1,500/month for all councils, custom watchlists, alerts within 24 hours, historical exports and a named analyst. Law firms and large developers pay for this. (Price changes are Huxley's call.)
3. **More feeds on the same pipeline.** `feeds.yaml` already supports this. Likely candidates: land development and housing (homebuilders and planning lawyers, a much bigger market), data centres and large loads, aggregates and mining, transmission.
4. **More provinces.** Alberta, BC and Nova Scotia run renewable procurements with municipal steps.

Honest timeline: $100k/month is a 2028-scale goal. The plan is built so every month has a measurable step toward it.

## Milestones
| By | Milestone | Leading indicators |
|---|---|---|
| Dec 18, 2026 | First paying subscriber | 10 trial readers, 3 calls booked |
| Mar 31, 2027 | $1,000/month | 250+ councils read, 30 trial readers, 4 issues a month with 5+ items |
| Jul 31, 2027 | $10,000/month | Enterprise tier live, second feed in beta, ranking top 5 for "ieso lt2" |
| 2028 | $100,000/month | 3–5 feeds, 2+ provinces, enterprise and data deals |

## Next 4 weeks: getting the first sale
1. **Named-person selling (Huxley, about 20 min a day).** *Started Nov 21: first 5 in `outreach/named_contacts.csv`; daily numbers in `ops/scoreboard.md`.* Every weekday the chief of staff prepares up to 5 named decision-makers. Each comes with a sourced reason, such as their project and their council's next meeting, plus a ready-to-paste LinkedIn note. Huxley sends them from his LinkedIn. Offer: free month, and "tell me which councils you need".
2. **Concierge coverage for early customers.** For the first 5 customers, cover any council they name, including CiviCweb ones, by Huxley reading those agendas himself or signing councilradaron@gmail.com up to the council's own agenda email notices. Bots still never crawl CiviCweb.
3. **CiviCweb permission.** *Nov 21: link updated to getcouncilradar.ca; Diligent has no partnership/API form, so `ops/civicweb_permission_request.md` now routes it through the iCompass support contact on diligent.com/support, with the "Request a demo" form as fallback. Queued for the browser desk in `ops/browser_queue.md`.* *Nov 23: no web form exists; the browser desk now sends the email to customers@icompasstech.com from Gmail's web UI (queued).*
4. **Timely hooks.** Use live events (the Neoen Saugeen Shores BESS rezoning on Nov 23, new support resolutions) as the reason to reach out that week. *Nov 24: LLT RFP proposals are due Nov 26 (new guide at /guides/long-lead-time-rfp/); Tweed council takes a mayor's BESS notice of motion on Nov 26.*
5. **Distribution.** Weekly drafts of Bluesky, LinkedIn and Reddit posts built from public decisions and guides. Weekly link-building pitches to the prospects in `docs/seo/link_prospects.csv`, drafted in Gmail for Huxley to send.
6. **Warm replies get answered the same day.** The chief of staff drafts a reply in Gmail and pings Huxley.
7. **Fix wrapped links (found Nov 23).** The Gmail connector rewrites every link in every email we send to google.com/url (`ops/gmail_link_wrapping.md`). Huxley picks a sending option; until then, links work but show a Google redirect notice after about a day. *Nov 23: decided (link-free cold email, Buttondown for the issue). Nov 24: Buttondown delivery is built and tested (`ops/buttondown_migration.md`); it waits only for the `BUTTONDOWN_API_KEY` secret.*

## The agent team
| Agent | When (Toronto) | Job | Sends email? |
|---|---|---|---|
| Weekly issue | Mon 7:23 am | Reads councils, renders and sends the issue to subscribers and trial readers | Yes (subscribers only) |
| LT2 Window 2 watch | Mon 7:41 am | Watches the IESO for Window 2 changes, opens a PR | No |
| Daily outreach | Weekdays 1:37 pm | Cold email within the hard limits in `ops/outreach_task.md` | Yes (approved limits) |
| Weekly business review | Fri 2:43 pm | Finds the bottleneck, ships one improvement, reports | Report only |
| **Chief of staff (logistics)** | Weekdays 7:52 am | Checks every agent's health and fixes what it can, keeps the plan and scoreboard, answers routine warm replies itself (trials, factual questions, booking calls on Huxley's calendar), hands named contacts with published emails to outreach, and sends a short "Needs you" list (at most 3 items) | Yes, replies to prospects who wrote in; escalations stay drafts |
| **Social posts** | Tue 4:11 pm | 3–5 Bluesky posts a week, queued for the browser desk to publish; optional LinkedIn and Reddit drafts | Only to Huxley |
| **Link building** | Wed 3:17 pm | Researches 3–5 link prospects and drafts pitches in Gmail | Drafts only |
| **Expansion research** | Thu 7:26 pm | One sized, sourced memo a week on the path to $100k (new feed, province or tier). Prototypes a promising feed behind `enabled: false` and merges it if tests pass | Only to Huxley |
| **Browser desk** | Daily 8:13 pm, on Huxley's Mac | Works `ops/browser_queue.md`: publishes Bluesky posts, submits organizations' contact forms (e.g. the CiviCweb request), checks Search Console and GA4 | Only to Huxley, when something needs him |

**Owner directive (Nov 21): Huxley's intervention is a last resort.** Every agent tries to finish a task with its own tools first. Anything that needs a browser goes to `ops/browser_queue.md` for the browser desk. Still reserved for Huxley: passwords, 2FA codes and payment details; spending money; creating accounts; accepting terms; prices and Stripe; legal, contract or discount commitments; CAPTCHAs and bot checks; sending link-building pitches (one click each, from Gmail drafts); and his personal LinkedIn and Reddit. Agents also honour robots.txt and never edit scheduled tasks.

## Scoreboard (chief of staff updates weekly)
Paying subscribers · MRR · trial readers · calls booked · named contacts sent · cold emails sent · replies · councils read · items per issue · organic clicks.
