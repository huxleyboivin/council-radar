# Improvements log

The weekly business review appends one entry per run (date, what changed, why, result to check next week).
Read this first so improvements build on each other instead of repeating.

## 2026-11-16/17 (manual sessions)
- Broadened energy keyword patterns; reads re-scan when patterns change; `radar run --refresh`. Issue went from 0 to 3 items.
- Added `agenda-check` diagnostic workflow.
- Found 119 CiviCweb councils uncovered; their robots.txt disallows bots, so no scraper. Options: agenda email subscriptions (human sign-up), or ask iCompass for permission.
- Added IESO LT2 Window 1 winners to prospects; set up weekly outreach task (Tuesdays, cap 10 new).
- 2026-11-17: Landing hero is now a "Check your council" lookup (441 municipalities; public decisions, next meetings, subscriber-item counts) with a watchlist that pre-fills the trial email and tags Stripe checkouts with `client_reference_id=w_<councils>`. Check next week: trial emails should arrive with council lists; Stripe sessions should carry a client reference ID; any "not read yet" councils people request.
- 2026-11-18: Personalized "Your Monday email" preview at `site/brief.html?for=<Company>&c=<councils>`, reading `site/councils.json` (rebuilt on each deploy). The homepage watchlist's main button and the sample issue now lead there; outreach template A sends each developer a preview for their own municipality instead of the generic sample. Published sample signals (e.g. RES in Wellesley, Prowind in Minto) now show as "Early signal" in the lookup. Fixed: the `pub-hamilton` portal was labelled Township of Hamilton; it is City of Hamilton (YAML and 25 meeting rows). Check next week: trial emails with subjects starting "Free trial: <Company>" (from the preview), and Stripe sessions with `client_reference_id` starting `b_`. To do: check whether Town of Minto (Prowind's project) is on eScribe and add it.
