# Improvements log

The weekly business review appends one entry per run (date, what changed, why, result to check next week).
Read this first so improvements build on each other instead of repeating.

## 2026-11-16/17 (manual sessions)
- Broadened energy keyword patterns; reads re-scan when patterns change; `radar run --refresh`. Issue went from 0 to 3 items.
- Added `agenda-check` diagnostic workflow.
- Found 119 CiviCweb councils uncovered; their robots.txt disallows bots, so no scraper. Options: agenda email subscriptions (human sign-up), or ask iCompass for permission.
- Added IESO LT2 Window 1 winners to prospects; set up weekly outreach task (Tuesdays, cap 10 new).
- 2026-11-17: Landing hero is now a "Check your council" lookup (441 municipalities; public decisions, next meetings, subscriber-item counts) with a watchlist that pre-fills the trial email and tags Stripe checkouts with `client_reference_id=w_<councils>`. Check next week: trial emails should arrive with council lists; Stripe sessions should carry a client reference ID; any "not read yet" councils people request.
